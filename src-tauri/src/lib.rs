use std::fs::{self, OpenOptions};
use std::io::{Read, Write};
use std::net::{SocketAddr, TcpStream};
use std::path::Path;
use std::sync::Mutex;
use std::thread;
use std::time::Duration;
use tauri::{Manager, RunEvent};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

struct SidecarState {
    child: Mutex<Option<CommandChild>>,
}

fn append_log(path: &Path, message: &str) {
    if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(path) {
        let _ = writeln!(file, "{message}");
    }
}

fn backend_is_ready(versao: Option<&str>) -> bool {
    let address = SocketAddr::from(([127, 0, 0, 1], 8000));
    let mut stream = match TcpStream::connect_timeout(&address, Duration::from_millis(500)) {
        Ok(stream) => stream,
        Err(_) => return false,
    };

    let _ = stream.set_read_timeout(Some(Duration::from_millis(500)));
    let _ = stream.set_write_timeout(Some(Duration::from_millis(500)));

    if stream
        .write_all(b"GET /health HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n")
        .is_err()
    {
        return false;
    }

    let mut response = String::new();
    if stream.read_to_string(&mut response).is_err() || !response.starts_with("HTTP/1.1 200 ") {
        return false;
    }
    let Some((_, corpo)) = response.split_once("\r\n\r\n") else {
        return false;
    };
    let Ok(saude) = serde_json::from_str::<serde_json::Value>(corpo) else {
        return false;
    };
    saude["ok"].as_bool() == Some(true)
        && saude["db_ready"].as_bool() == Some(true)
        && versao.is_none_or(|esperada| saude["desktopVersion"].as_str() == Some(esperada))
}

#[cfg(windows)]
fn encerrar_sidecar_anterior(log_path: &Path) {
    use std::os::windows::process::CommandExt;

    let Ok(executavel) = std::env::current_exe() else {
        return;
    };
    let Some(instalacao) = executavel.parent() else {
        return;
    };
    let Some(sistema) = std::env::var_os("SystemRoot") else {
        return;
    };
    let powershell = Path::new(&sistema).join("System32/WindowsPowerShell/v1.0/powershell.exe");
    // a instalação antiga pode deixar o processo interno do PyInstaller na porta
    let comando = r#"
        Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
          ForEach-Object { Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue } |
          Where-Object { $_.Path -eq $env:LEAD_SCRAPER_SIDECAR_PATH } |
          Stop-Process -ErrorAction Stop
    "#;
    let resultado = std::process::Command::new(powershell)
        .args(["-NoProfile", "-NonInteractive", "-Command", comando])
        .env("LEAD_SCRAPER_SIDECAR_PATH", instalacao.join("scraper-sidecar.exe"))
        .creation_flags(0x08000000)
        .output();
    if !resultado.is_ok_and(|saida| saida.status.success()) {
        append_log(log_path, "não foi possível encerrar o sidecar anterior");
    }
}

fn encerrar_sidecar(child: CommandChild) {
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        if let Some(sistema) = std::env::var_os("SystemRoot") {
            let taskkill = Path::new(&sistema).join("System32/taskkill.exe");
            if std::process::Command::new(taskkill)
                .args(["/PID", &child.pid().to_string(), "/T", "/F"])
                .creation_flags(0x08000000)
                .output()
                .is_ok_and(|saida| saida.status.success())
            {
                return;
            }
        }
    }
    let _ = child.kill();
}

fn wait_for_backend(log_path: &Path, versao: Option<&str>) -> bool {
    for attempt in 1..=80 {
        if backend_is_ready(versao) {
            append_log(log_path, &format!("backend ready after {attempt} checks"));
            return true;
        }
        thread::sleep(Duration::from_millis(250));
    }

    append_log(log_path, "backend did not answer /health in time");
    false
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .manage(SidecarState {
            child: Mutex::new(None),
        })
        .setup(|app| {
            let app_data_dir = app.path().app_data_dir()?;
            fs::create_dir_all(&app_data_dir)?;

            let db_path = app_data_dir.join("banco.db");
            let launch_log_path = app_data_dir.join("sidecar-launch.log");
            let sidecar_log_path = app_data_dir.join("sidecar.log");
            let resource_dir = app.path().resource_dir()?;
            let playwright_browsers = resource_dir.join("ms-playwright");
            append_log(&launch_log_path, "starting lead-scraper app setup");
            append_log(&launch_log_path, &format!("DB_PATH={}", db_path.display()));
            append_log(
                &launch_log_path,
                &format!("PLAYWRIGHT_BROWSERS_PATH={}", playwright_browsers.display()),
            );

            let versao = app.package_info().version.to_string();
            let esperada = (!cfg!(debug_assertions)).then_some(versao.as_str());
            if !backend_is_ready(esperada) {
                #[cfg(windows)]
                if esperada.is_some() && backend_is_ready(None) {
                    encerrar_sidecar_anterior(&launch_log_path);
                }
                append_log(&launch_log_path, "backend offline; spawning scraper-sidecar");
                match app
                    .shell()
                    .sidecar("scraper-sidecar")
                    .and_then(|sidecar| {
                        sidecar
                            .env("DB_PATH", db_path.to_string_lossy().to_string())
                            .env("LEAD_SCRAPER_DESKTOP_VERSION", &versao)
                            .env(
                                "PLAYWRIGHT_BROWSERS_PATH",
                                playwright_browsers.to_string_lossy().to_string(),
                            )
                            .spawn()
                    })
                {
                    Ok((mut rx, child)) => {
                        let log_path = sidecar_log_path.clone();
                        tauri::async_runtime::spawn(async move {
                            while let Some(event) = rx.recv().await {
                                match event {
                                    CommandEvent::Stdout(line) => append_log(
                                        &log_path,
                                        &format!("stdout: {}", String::from_utf8_lossy(&line)),
                                    ),
                                    CommandEvent::Stderr(line) => append_log(
                                        &log_path,
                                        &format!("stderr: {}", String::from_utf8_lossy(&line)),
                                    ),
                                    CommandEvent::Terminated(payload) => append_log(
                                        &log_path,
                                        &format!("terminated: {:?}", payload),
                                    ),
                                    other => append_log(&log_path, &format!("event: {:?}", other)),
                                }
                            }
                        });

                        let state = app.state::<SidecarState>();
                        *state.child.lock().expect("sidecar state lock poisoned") = Some(child);
                        append_log(&launch_log_path, "scraper-sidecar spawned");
                    }
                    Err(error) => {
                        append_log(
                            &launch_log_path,
                            &format!("failed to start scraper-sidecar: {error}"),
                        );
                        eprintln!("failed to start scraper-sidecar: {error}");
                    }
                }
            } else {
                append_log(&launch_log_path, "backend already healthy on 127.0.0.1:8000");
            }

            if !wait_for_backend(&launch_log_path, esperada) {
                eprintln!("scraper-sidecar did not answer /health in time");
            }

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building Tauri application")
        .run(|app_handle, event| {
            if matches!(event, RunEvent::ExitRequested { .. } | RunEvent::Exit) {
                let state = app_handle.state::<SidecarState>();
                let mut lock = state.child.lock().expect("sidecar state lock poisoned");
                if let Some(child) = lock.take() {
                    encerrar_sidecar(child);
                }
            }
        });
}
