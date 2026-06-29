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

fn backend_is_ready() -> bool {
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
    stream.read_to_string(&mut response).is_ok()
        && response.starts_with("HTTP/1.1 200")
        && response.contains("\"ok\"")
}

fn wait_for_backend(log_path: &Path) -> bool {
    for attempt in 1..=80 {
        if backend_is_ready() {
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
        .plugin(tauri_plugin_shell::init())
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

            if !backend_is_ready() {
                append_log(&launch_log_path, "backend offline; spawning scraper-sidecar");
                match app
                    .shell()
                    .sidecar("scraper-sidecar")
                    .and_then(|sidecar| {
                        sidecar
                            .env("DB_PATH", db_path.to_string_lossy().to_string())
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

            if !wait_for_backend(&launch_log_path) {
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
                    let _ = child.kill();
                }
            }
        });
}