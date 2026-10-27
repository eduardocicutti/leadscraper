import axios from "axios";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Botao } from "../../components/ui/Botao";
import { mensagemErroCrm, salvarCrm } from "../../services/crm";

export function ConverterLead({ leadId }: { leadId: number }) {
  const cliente = useQueryClient();
  const [salvando, definirSalvando] = useState(false);
  const [concluido, definirConcluido] = useState(false);
  const [erro, definirErro] = useState("");
  const [candidatas, definirCandidatas] = useState<
    { id: string; nome: string }[]
  >([]);
  async function converter(empresaId?: string) {
    definirSalvando(true);
    definirErro("");
    try {
      await salvarCrm(`selecionados/${leadId}/converter`, { empresaId });
      definirConcluido(true);
      definirCandidatas([]);
      void cliente.invalidateQueries({ queryKey: ["crm"] });
    } catch (falha) {
      definirErro(mensagemErroCrm(falha));
      if (axios.isAxiosError(falha)) {
        const resposta: unknown = falha.response?.data;
        if (
          typeof resposta === "object" &&
          resposta !== null &&
          "candidatas" in resposta &&
          Array.isArray(resposta.candidatas)
        ) {
          definirCandidatas(
            resposta.candidatas.flatMap((item: unknown) =>
              typeof item === "object" &&
              item !== null &&
              "id" in item &&
              typeof item.id === "string" &&
              "nome" in item &&
              typeof item.nome === "string"
                ? [{ id: item.id, nome: item.nome }]
                : [],
            ),
          );
        }
      }
    } finally {
      definirSalvando(false);
    }
  }
  return (
    <div>
      <Botao
        carregando={salvando}
        disabled={concluido}
        onClick={() => void converter()}
      >
        {concluido ? "No CRM" : "Adicionar ao CRM"}
      </Botao>
      {erro && <p role="alert">{erro}</p>}
      {candidatas.map((empresa) => (
        <Botao
          key={empresa.id}
          carregando={salvando}
          onClick={() => void converter(empresa.id)}
        >
          Vincular a {empresa.nome}
        </Botao>
      ))}
    </div>
  );
}
