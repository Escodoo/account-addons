# Orientações para contribuições

Estas instruções se aplicam ao repositório `Escodoo/account-addons`. As convenções de
postagem abaixo foram observadas no projeto; não representam regras universais da OCA ou
de outros projetos open source.

## Antes de implementar

- Leia a issue, seus comentários e as instruções do módulo afetado.
- Confirme a versão do Odoo e a branch de destino. Esta branch corresponde à 18.0.
- Confira os remotos e procure branches e PRs existentes para o mesmo problema antes de
  criar outra implementação. Preserve alterações e commits existentes.
- Para trabalhos relacionados a repositórios da OCA, verifique o repositório de origem,
  a correspondência do fork e o acesso real de escrita. Priorize o fork da Escodoo
  quando existir e puder ser usado. Use um fork pessoal somente quando essa opção não
  estiver disponível. Não presuma permissões.
- Mantenha a alteração focada no problema. Separe mudanças independentes em branches e
  PRs próprios.

## Implementação e validação

- Siga os padrões do módulo e preserve a licença aplicável.
- Para correções de comportamento, adicione testes de regressão pertinentes. Quando
  útil, confirme que o teste falha com o código original e passa com a correção.
- Execute os testes apropriados à mudança e os hooks definidos em
  `.pre-commit-config.yaml` para os arquivos alterados.
- Consulte `.github/workflows/` para conhecer as verificações da CI. Diferencie
  resultados locais dos resultados de Odoo, OCB e demais checks no GitHub.
- Informe apenas operações e resultados confirmados. Registre limitações de acesso ou
  execução e não atribua uma falha à alteração sem evidências.

## Títulos e descrições de PR

- Use o formato observado: `[18.0][FIX] nome_do_modulo: descrição curta`. Ajuste a
  versão e a categoria (`ADD`, `IMP`, `MIG`, `REF`) ao trabalho real.
- Explique o problema e seu gatilho, o comportamento após a mudança e a validação
  realizada. Seja conciso e proporcional à complexidade da alteração.
- Inglês e português aparecem no projeto. Mantenha o texto consistente e siga eventuais
  instruções específicas do mantenedor.
- Inclua `Closes #NNN` quando o PR resolver a issue e seu fechamento no merge for
  apropriado.
- Ticket de projeto e `cc` aparecem em algumas contribuições, mas não devem ser tratados
  como obrigatórios sem instrução explícita. Não invente referências nem acrescente
  notificações sem pertinência e autorização.
- Antes de publicar, confira o diff, a branch de origem e a branch de destino.

## Atualizações nas issues

- Quando autorizado a comentar, use uma atualização curta com o link do PR.
- Enquanto o PR estiver aberto, prefira:
  `Correção proposta no #NNN. Aguardando revisão.`
- Acrescente os checks aprovados somente depois de verificar seus resultados.
- Depois do merge, pode usar: `Corrigido no #NNN.`
- Diferencie rascunho, pronto para revisão, aprovado, integrado e implantado. Merge e CI
  não comprovam implantação ou validação funcional no ambiente.
- Um pedido de revisão do texto não autoriza, por si só, publicar comentários.

## Referências e manutenção

Exemplos consultados em 28/10/2026:

- [PR #208](https://github.com/Escodoo/account-addons/pull/208): título e descrição
  técnica de uma correção.
- [PR #219](https://github.com/Escodoo/account-addons/pull/219): explicação do problema
  e das alterações de CI.
- [Issue #153](https://github.com/Escodoo/account-addons/issues/153) e
  [issue #91](https://github.com/Escodoo/account-addons/issues/91): comentários curtos
  de resolução com referência ao PR.

Revalide os exemplos e as instruções atuais antes de contribuir. Ao atualizar este
arquivo, separe requisitos explícitos de convenções observadas e preserve as fontes que
sustentam as orientações.
