import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Botao } from "../../components/ui/Botao";
import {
  ehConversao,
  empresasCandidatas,
  mensagemErroCrm,
  rotuloEmpresaCandidata,
  salvarCrm,
  type EmpresaCandidata,
} from "../../services/crm";
import { useAppStore } from "../../store";
import { idLegadoValido } from "../../utils/idLegadoValido";

export function ConverterLead({
  leadId,
  historicoId,
}: {
  leadId: number;
  historicoId?: number;
}) {
  const cliente = useQueryClient();
  const abrirEmpresa = useAppStore((estado) => estado.abrirEmpresa);
  const [estaSalvando, definirEstaSalvando] = useState(false);
  const [empresaVinculadaId, definirEmpresaVinculadaId] = useState<string | null>(
    null,
  );
  const [erro, definirErro] = useState("");
  const [candidatas, definirCandidatas] = useState<EmpresaCandidata[]>([]);
  const podeCadastrarSeparadamente =
    candidatas.length > 0 &&
    candidatas.every((candidata) => candidata.somenteTelefone);
  async function converter(
    empresaId?: string,
    confirmarTelefoneCompartilhado = false,
  ) {
    if (!idLegadoValido(leadId) || (historicoId !== undefined && !idLegadoValido(historicoId))) {
      definirErro("Não foi possível identificar o lead. Recarregue a lista.");
      return;
    }
    definirEstaSalvando(true);
    definirErro("");
    try {
      const caminho = historicoId
        ? `historico/${historicoId}/leads/${leadId}/converter`
        : `selecionados/${leadId}/converter`;
      const resposta = await salvarCrm(caminho, ehConversao, {
        empresaId,
        ...(confirmarTelefoneCompartilhado ? { confirmarTelefoneCompartilhado } : {}),
      });
      definirEmpresaVinculadaId(resposta.empresaId);
      definirCandidatas([]);
      void cliente.invalidateQueries({ queryKey: ["crm"] });
    } catch (falha) {
      definirErro(mensagemErroCrm(falha));
      const novasCandidatas = empresasCandidatas(falha);
      if ((!empresaId && !confirmarTelefoneCompartilhado) || novasCandidatas.length > 0)
        definirCandidatas(novasCandidatas);
    } finally {
      definirEstaSalvando(false);
    }
  }
  if (empresaVinculadaId)
    return (
      <div>
        <p role="status">Empresa vinculada ao CRM.</p>
        <Botao onClick={() => abrirEmpresa(empresaVinculadaId)}>
          Abrir empresa no CRM
        </Botao>
      </div>
    );

  return (
    <div className="whitespace-normal">
      <Botao
        carregando={estaSalvando}
        disabled={candidatas.length > 0}
        onClick={() => void converter()}
      >
        Adicionar ao CRM
      </Botao>
      {erro && <p role="alert">{erro}</p>}
      {candidatas.map((empresa) => (
        <Botao
          key={empresa.id}
          disabled={estaSalvando}
          onClick={() => void converter(empresa.id)}
        >
          Vincular a {rotuloEmpresaCandidata(empresa)}
        </Botao>
      ))}
      {podeCadastrarSeparadamente && (
        <Botao
          disabled={estaSalvando}
          onClick={() => void converter(undefined, true)}
        >
          Cadastrar empresa separadamente
        </Botao>
      )}
      {candidatas.length > 0 && (
        <Botao
          variante="discreto"
          disabled={estaSalvando}
          onClick={() => {
            definirCandidatas([]);
            definirErro("");
          }}
        >
          Cancelar vínculo
        </Botao>
      )}
    </div>
  );
}
