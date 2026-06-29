# Caçador de Leads — Adapti
 
Sistema de prospecção automática via Google Maps. Busca, qualifica e exporta leads no formato do modelo Julho.
 
---
 
## O que você precisa ter instalado
 
- **Python 3.10 ou mais novo** — [baixar aqui](https://www.python.org/downloads/)
- **Um destes navegadores:** Chrome, Edge ou Firefox
  - Edge — já vem instalado no Windows 10/11
  - Chrome — funciona em Windows, Mac e Linux
  - Firefox — funciona em Windows, Mac e Linux
  - Opera, Brave e outros não são suportados
---
 
## Instalação (só na primeira vez)
 
Abra o terminal (PowerShell no Windows, Terminal no Mac/Linux) e rode:
 
```
pip install fastapi uvicorn selenium webdriver-manager openpyxl
```
 
---
 
## Como rodar
 
### Windows
Dê dois cliques no arquivo **`rodar.bat`** dentro da pasta do projeto.
 
O navegador vai abrir sozinho em `http://localhost:8000`.
 
### Mac / Linux
Abra o terminal na pasta do projeto e rode:
 
```
python3 -m uvicorn main:app --port 8000
```
 
Depois abra `http://localhost:8000` no navegador.
 
---
 
## Como usar
 
1. **Selecione seu nome** no campo "Prospectador"
2. **Digite o segmento** que quer buscar (ex: clínicas odontológicas, academias, escritórios de advocacia)
3. **Digite a cidade e o estado**
4. **Escolha quantos leads** quer coletar (10, 20, 30 ou 50)
5. Clique em **Buscar** e aguarde — o sistema faz tudo sozinho
6. Quando terminar, clique em **Exportar Excel** para baixar a planilha
---
 
## O que vem na planilha
 
A planilha exportada segue o mesmo formato do modelo Julho, com:
 
- Nome do responsável (seu nome, preenchido automaticamente)
- Estágio atual (inicia em "Qualificação")
- Nome da empresa, telefone, ramo de atividade
- Porte da empresa (MEI, Micro, Pequena, Média ou Grande)
- Nota e número de avaliações no Google
- Score Adapti (0 a 100) e temperatura ( Quente /  Morno /  Frio)
- Link do WhatsApp com mensagem pronta da Adapti
- Link direto para o Google Maps
---
 
## WhatsApp
 
Quando o número coletado for de celular, aparece um botão ** Enviar** na tela.
 
Ao clicar, o WhatsApp abre direto com a mensagem já escrita com o nome da empresa. É só enviar.
 
---
 
## Sistema de Score
 
Cada lead recebe uma pontuação de 0 a 100:
 
| Critério | Pontos |
|---|---|
| Empresa sem site (oportunidade para Adapti) | 25 pts |
| Avaliações no Google (quanto mais, melhor) | até 20 pts |
| Nota no Google (quanto maior, melhor) | até 15 pts |
| Segmento com potencial digital alto | 30 pts |
| Porte da empresa | até 15 pts |
 
** Quente** = 70 pontos ou mais  
** Morno** = 45 a 69 pontos  
** Frio** = menos de 45 pontos  
 
---
 
## Problemas comuns
 
**"uvicorn não é reconhecido"**  
Use `python -m uvicorn main:app --port 8000` em vez de só `uvicorn`.
 
**"Nenhum navegador encontrado"**  
Instale o Chrome ou confirme que o Edge está atualizado.
 
**A busca demorou muito ou não encontrou nada**  
O Google Maps pode ter limitado o acesso temporariamente. Aguarde alguns minutos e tente de novo com um segmento diferente.
 
**A planilha não exportou**  
A busca precisa terminar completamente antes de exportar. Aguarde a mensagem "Concluído!" aparecer na tela.
 