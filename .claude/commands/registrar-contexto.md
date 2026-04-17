Pergunte ao usuário um de cada vez:

1. "Que tipo de contribuição você quer registrar?"
   Opções:
   - Architecture decision
   - Technical discussion
   - Cross-team alignment
   - Technical influence (shaped direction without writing code)
   - Incident response
   - Mentorship or knowledge sharing
   - Other

2. "Descreva o que aconteceu. Pode ser longo — cole trechos de conversa,
   resumo de reunião, slack thread, ou escreva livremente."

3. "Qual foi o impacto ou resultado? (pode deixar em branco se ainda não sabe)"

4. "Quando aconteceu? (ex: hoje, 10/04, semana passada — qualquer formato)"

5. "Tem algum ticket, PR ou pessoa envolvida que vale mencionar? (opcional)"

Com as respostas em mãos, execute:
!python main.py registrar --type "RESPOSTA1" --description "RESPOSTA2" --impact "RESPOSTA3" --date "RESPOSTA4" --references "RESPOSTA5"

Após a execução, confirme para o usuário que a entrada foi salva e em qual arquivo.
