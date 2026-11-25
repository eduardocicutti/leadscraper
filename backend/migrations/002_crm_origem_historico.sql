CREATE TABLE crm_origem_historico (
    id TEXT PRIMARY KEY,
    empresaId TEXT NOT NULL REFERENCES crm_empresa(id),
    organizationId TEXT NOT NULL,
    historicoId INTEGER NOT NULL,
    leadId INTEGER NOT NULL,
    historicoCriadoEm TEXT NOT NULL,
    nomeOriginal TEXT NOT NULL,
    urlMapsOriginal TEXT NOT NULL,
    createdBy TEXT NOT NULL,
    createdAt TEXT NOT NULL,
    UNIQUE (organizationId, historicoId, leadId, historicoCriadoEm)
);
