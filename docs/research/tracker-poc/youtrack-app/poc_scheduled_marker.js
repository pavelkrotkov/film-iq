// Isolated demonstration: this rule updates one synthetic marker only once.
// It never interprets provider data, makes external calls, or sends messages.
const entities = require('@jetbrains/youtrack-scripting-api/entities');

exports.rule = entities.Issue.onSchedule({
  title: 'FilmIQ POC: mark one synthetic scheduled check',
  search: 'issue id: FILMPOC-1',
  cron: '0 * * * * ?',
  muteUpdateNotifications: true,
  modifyUpdatedProperties: true,
  guard: (ctx) => ctx.issue.project.key === 'FILMPOC' &&
    ctx.issue.id === 'FILMPOC-1' && ctx.issue.fields.Fixture === 91001 &&
    !ctx.issue.fields.ScheduleMarker,
  action: (ctx) => { ctx.issue.fields.ScheduleMarker = 'synthetic check processed'; },
  requirements: {
    Fixture: { name: 'FilmIQ Fixture ID', type: entities.Field.integerType },
    ScheduleMarker: { name: 'FilmIQ POC Schedule Marker', type: entities.Field.stringType },
  },
});
