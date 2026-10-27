import {
  Search,
  ContactRound,
  Building2,
  UsersRound,
  Handshake,
  CalendarDays,
  FolderClosed,
  History,
  Sheet,
  File,
  Users,
  Settings,
  Info,
  type LucideIcon,
} from "lucide-react";

export type Tela =
  | "search"
  | "selected"
  | "companies"
  | "contacts"
  | "opportunities"
  | "activities"
  | "projects"
  | "history"
  | "spreadsheets"
  | "files"
  | "team"
  | "settings"
  | "about"
  | "agent";

export interface ItemNavegacao {
  tela: Tela;
  titulo: string;
  descricao: string;
  icone: LucideIcon;
  grupo: number;
  fase?: string;
}

export const NAVEGACAO: ItemNavegacao[] = [
  {
    tela: "search",
    titulo: "Prospecção",
    descricao: "Encontre empresas e organize sua próxima abordagem.",
    icone: Search,
    grupo: 0,
  },
  {
    tela: "selected",
    titulo: "Leads",
    descricao: "Sua lista preferencial, mensagens e contatos selecionados.",
    icone: ContactRound,
    grupo: 0,
  },
  {
    tela: "companies",
    titulo: "Empresas",
    descricao: "Centralize as informações de cada empresa.",
    icone: Building2,
    grupo: 0,
    fase: "2",
  },
  {
    tela: "contacts",
    titulo: "Contatos",
    descricao: "Pessoas, telefones e histórico de relacionamento.",
    icone: UsersRound,
    grupo: 0,
    fase: "2",
  },
  {
    tela: "opportunities",
    titulo: "Oportunidades",
    descricao: "Acompanhe o andamento das negociações.",
    icone: Handshake,
    grupo: 0,
    fase: "4",
  },
  {
    tela: "activities",
    titulo: "Atividades",
    descricao: "Organize tarefas, retornos e lembretes de pós-venda.",
    icone: CalendarDays,
    grupo: 0,
    fase: "2 e 4",
  },
  {
    tela: "projects",
    titulo: "Projetos",
    descricao: "Acompanhe projetos comerciais e entregas aos clientes.",
    icone: FolderClosed,
    grupo: 0,
    fase: "4",
  },
  {
    tela: "history",
    titulo: "Histórico",
    descricao: "Consulte, exporte e atualize suas prospecções passadas.",
    icone: History,
    grupo: 1,
  },
  {
    tela: "spreadsheets",
    titulo: "Planilhas",
    descricao: "Importe contatos e exporte suas listas de prospecção.",
    icone: Sheet,
    grupo: 1,
  },
  {
    tela: "files",
    titulo: "Arquivos",
    descricao: "Documentos vinculados aos seus clientes e projetos.",
    icone: File,
    grupo: 1,
    fase: "4 a 6",
  },
  {
    tela: "team",
    titulo: "Equipe",
    descricao: "Membros, cargos e organização da equipe.",
    icone: Users,
    grupo: 1,
    fase: "6",
  },
  {
    tela: "settings",
    titulo: "Configurações",
    descricao: "Deixe a interface do seu jeito.",
    icone: Settings,
    grupo: 2,
  },
  {
    tela: "about",
    titulo: "Sobre",
    descricao: "Versão, diagnóstico e ferramentas de manutenção.",
    icone: Info,
    grupo: 2,
  },
];
