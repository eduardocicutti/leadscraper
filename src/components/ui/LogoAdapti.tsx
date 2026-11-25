import logoClaro from "../../assets/adapti-claro.png";
import logoEscuro from "../../assets/adapti-escuro.png";

export function LogoAdapti() {
  return (
    <span className="logo-adapti" aria-hidden="true">
      <img className="logo-adapti-claro" src={logoClaro} alt="" width={360} height={246} />
      <img className="logo-adapti-escuro" src={logoEscuro} alt="" width={360} height={246} />
    </span>
  );
}
