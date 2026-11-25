import { useState, type FormEvent } from "react";
import { Botao } from "../../components/ui/Botao";
import {
  ehQualificacao,
  mensagemErroCrm,
  salvarCrm,
  type Qualificacao,
} from "../../services/crm";

export function QualificacaoLead({
  empresaId,
  qualificacao,
  atualizar,
}: {
  empresaId: string;
  qualificacao: Qualificacao;
  atualizar: () => void;
}) {
  const [situacao, definirSituacao] = useState(qualificacao.situacao);
  const [motivo, definirMotivo] = useState(qualificacao.motivo);
  const [estaSalvando, definirEstaSalvando] = useState(false);
  const [erro, definirErro] = useState("");
  const [sucesso, definirSucesso] = useState(false);
  async function salvar(evento: FormEvent) {
    evento.preventDefault();
    definirEstaSalvando(true);
    definirErro("");
    definirSucesso(false);
    try {
      await salvarCrm(
        `empresas/${empresaId}/qualificacao`,
        ehQualificacao,
        { situacao, motivo, version: qualificacao.version },
        true,
      );
      definirSucesso(true);
      atualizar();
    } catch (falha) {
      definirErro(mensagemErroCrm(falha));
    } finally {
      definirEstaSalvando(false);
    }
  }
  return (
    <section className="painel crm-formulario">
      <h2>Qualificação do lead</h2>
      <form onSubmit={(evento) => void salvar(evento)}>
        <div className="crm-campos">
          <label className="campo">
            <span>Qualificação</span>
            <select
              value={situacao}
              onChange={(evento) => {
                definirSituacao(
                  evento.target.value as Qualificacao["situacao"],
                );
                definirSucesso(false);
              }}
            >
              <option value="novo">Novo</option>
              <option value="analise">Em análise</option>
              <option value="qualificado">Qualificado</option>
              <option value="desqualificado">Desqualificado</option>
            </select>
          </label>
          <label className="campo">
            <span>Motivo / observação</span>
            <textarea
              value={motivo}
              onChange={(evento) => {
                definirMotivo(evento.target.value);
                definirSucesso(false);
              }}
              maxLength={1000}
              required={situacao === "desqualificado"}
            />
          </label>
        </div>
        <p>
          Qualificar não registra abordagem nem cria negociação. A conversão em
          oportunidade será disponibilizada com o pipeline.
        </p>
        {erro && (
          <p role="alert" className="aviso">
            {erro}
          </p>
        )}
        {sucesso && <p role="status">Qualificação salva.</p>}
        <Botao type="submit" variante="primario" carregando={estaSalvando}>
          Salvar qualificação
        </Botao>
      </form>
    </section>
  );
}
