# Auditoria de 25/11/2026

No agente d72ebe8, o SQLite contém 68 registros. O FAQ contém 46 ocorrências de “Regra proposta:”. A janela da API termina no meio da pergunta sobre cadastro de motorista (posição 450); no Streamlit, as janelas de 850 caracteres também ignoram as fronteiras das respostas. Os dois clientes consultam índices diferentes e sempre enviam os vizinhos mais próximos, mesmo sem evidência de relevância. O chat aceita histórico arbitrário na API e mistura a última pergunta com um assunto novo. Não há conjunto rotulado nem histórico real autorizado para avaliação.

O FAQ afirma atualização do GPS a cada dois segundos. O Android distingue estados ATUALIZADA, DESATUALIZADA e SEM_LOCALIZACAO. O texto antigo trata embarque como proposta, mas a Home distingue aguardando, embarcado e desembarcado. A proposta de gestão de frotas não deve virar instrução de uso.

Referências de código consultadas em modo de leitura:

* Android 2710389: src/services/passageiroHome.ts, src/services/rastreamento.ts, src/app/entrar-turma.tsx, src/components/passageiro/SeletorPresenca.tsx, src/app/(auth), src/app/(tabs)/perfil.tsx.
* Backend fab9f11: controladores de presença, embarque, convite, posição e rota pública em src/main/java/com/bevans/controller.
* Web 5409055: app/lib/conhecimento-bevans.mjs e app/api/assistente/route.js. O site mantém implementação própria e não chama esta API.
