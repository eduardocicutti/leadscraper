CREATE TABLE crm_empresa (
    id TEXT PRIMARY KEY,
    organizationId TEXT NOT NULL,
    nome TEXT NOT NULL,
    nomeNormalizado TEXT NOT NULL,
    cnpj TEXT,
    segmento TEXT NOT NULL DEFAULT '',
    cidade TEXT NOT NULL DEFAULT '',
    cidadeNormalizada TEXT NOT NULL DEFAULT '',
    uf TEXT NOT NULL DEFAULT '',
    site TEXT NOT NULL DEFAULT '',
    urlMaps TEXT NOT NULL DEFAULT '',
    responsavel TEXT NOT NULL,
    arquivada INTEGER NOT NULL DEFAULT 0 CHECK (arquivada IN (0, 1)),
    createdBy TEXT NOT NULL,
    updatedBy TEXT NOT NULL,
    createdAt TEXT NOT NULL,
    updatedAt TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    UNIQUE (organizationId, cnpj)
);
CREATE INDEX crm_empresa_busca ON crm_empresa(organizationId, nomeNormalizado);
CREATE INDEX crm_empresa_responsavel ON crm_empresa(organizationId, responsavel);
CREATE TABLE crm_contato (
    id TEXT PRIMARY KEY,
    empresaId TEXT NOT NULL REFERENCES crm_empresa(id),
    organizationId TEXT NOT NULL,
    nome TEXT NOT NULL,
    nomeNormalizado TEXT NOT NULL,
    cargo TEXT NOT NULL DEFAULT '',
    telefone TEXT NOT NULL DEFAULT '',
    telefoneNormalizado TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    createdBy TEXT NOT NULL,
    updatedBy TEXT NOT NULL,
    createdAt TEXT NOT NULL,
    updatedAt TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX crm_contato_telefone ON crm_contato(organizationId, telefoneNormalizado);
CREATE INDEX crm_contato_empresa ON crm_contato(organizationId, empresaId);
CREATE TABLE crm_lead (
    id TEXT PRIMARY KEY,
    empresaId TEXT NOT NULL UNIQUE REFERENCES crm_empresa(id),
    organizationId TEXT NOT NULL,
    situacao TEXT NOT NULL DEFAULT 'novo' CHECK (situacao IN ('novo','analise','qualificado','desqualificado')),
    motivo TEXT NOT NULL DEFAULT '',
    createdBy TEXT NOT NULL,
    updatedBy TEXT NOT NULL,
    createdAt TEXT NOT NULL,
    updatedAt TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE crm_atividade (
    id TEXT PRIMARY KEY,
    empresaId TEXT NOT NULL REFERENCES crm_empresa(id),
    organizationId TEXT NOT NULL,
    titulo TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('ligacao','whatsapp','email','reuniao','tarefa','lembrete')),
    situacao TEXT NOT NULL CHECK (situacao IN ('pendente','concluida','cancelada')),
    descricao TEXT NOT NULL DEFAULT '',
    resultado TEXT NOT NULL DEFAULT '',
    responsavel TEXT NOT NULL,
    prazoData TEXT,
    concluidaEm TEXT,
    autorNome TEXT NOT NULL,
    createdBy TEXT NOT NULL,
    updatedBy TEXT NOT NULL,
    createdAt TEXT NOT NULL,
    updatedAt TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX crm_atividade_empresa ON crm_atividade(organizationId, empresaId, createdAt);
CREATE INDEX crm_atividade_prazo ON crm_atividade(organizationId, situacao, prazoData);
CREATE TABLE crm_evento (
    id TEXT PRIMARY KEY,
    empresaId TEXT NOT NULL REFERENCES crm_empresa(id),
    organizationId TEXT NOT NULL,
    tipo TEXT NOT NULL,
    descricao TEXT NOT NULL,
    autorId TEXT NOT NULL,
    autorNome TEXT NOT NULL,
    createdAt TEXT NOT NULL
);
CREATE INDEX crm_evento_empresa ON crm_evento(organizationId, empresaId, createdAt);
CREATE TABLE crm_origem_selecionada (
    selectedId INTEGER PRIMARY KEY,
    empresaId TEXT NOT NULL REFERENCES crm_empresa(id),
    organizationId TEXT NOT NULL,
    nomeOriginal TEXT NOT NULL,
    createdBy TEXT NOT NULL,
    createdAt TEXT NOT NULL
);
