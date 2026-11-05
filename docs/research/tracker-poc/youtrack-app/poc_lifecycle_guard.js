// Isolated demonstration: only fixture 91001 on FILMPOC-1 is affected.
// The workflow does not modify fields or send notifications.
const entities = require('@jetbrains/youtrack-scripting-api/entities');
const workflow = require('@jetbrains/youtrack-scripting-api/workflow');

exports.rule = entities.Issue.onChange({
  title: 'FilmIQ POC: guard a synthetic lifecycle transition',
  guard: (ctx) => ctx.issue.project.key === 'FILMPOC' &&
    ctx.issue.id === 'FILMPOC-1' && ctx.issue.fields.Fixture === 91001 &&
    ctx.issue.fields.isChanged(ctx.Lifecycle),
  action: (ctx) => {
    const fields = ctx.issue.fields;
    if (fields.was(ctx.Lifecycle, ctx.Lifecycle.Archived) &&
        fields.becomes(ctx.Lifecycle, ctx.Lifecycle.Discovery)) {
      workflow.check(false, 'Synthetic POC: move Archived to Evaluation before Discovery.');
    }
  },
  requirements: {
    Fixture: { name: 'FilmIQ Fixture ID', type: entities.Field.integerType },
    Lifecycle: {
      name: 'FilmIQ Lifecycle', type: entities.State.fieldType,
      Archived: {}, Discovery: {},
    },
  },
});
