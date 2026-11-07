# YouTrack recovery: untested rehearsal

The existing local backup is not evidence of a successful restore. It contains
personal data, so it is not a suitable fixture for an isolated fictional test.
No fictional YouTrack server was started for this investigation, and recovery of
issues, attachments, the FilmIQ app and its app-owned properties remains untested.

JetBrains' [Docker restore instructions](https://www.jetbrains.com/help/youtrack/server/restore-docker-image-installation.html)
require the same or a newer YouTrack version and direct the operator to launch
with empty data and configuration directories, place the backup in the mapped
backup directory, and select it as the upgrade source in the configuration
wizard. The user must be able to review any setup/license prompt. A rehearsal
should use new directories and a separate server, never empty the running POC's
directories. The [backup documentation](https://www.jetbrains.com/help/youtrack/server/back-up-the-database.html)
states that a backup contains a database snapshot and attachments; it does not
by itself establish that this POC's app-owned properties restore correctly.

For useful evidence, first create a fictional-only source instance containing a
film, its custom fields, a comment, an attachment, and a FilmIQ user property.
Take its backup through YouTrack, restore that archive to a separate fictional
instance via the supported wizard, then verify each item and restart the
restored instance. Record the exact image version, commands, results and any
errors. Do not use or expose the real POC's backup or credentials.

On November 6, Docker reported 7.75 GiB total. Its running YouTrack container
used about 2.02 GiB and the other listed containers used about 2.0 GiB combined;
this was a single sample, not a capacity test. Starting another YouTrack could
compete with the POC and Immich, so no extra server was started. An empty
project-local fixture directory was retained; its dedicated empty Docker
network was removed. No restore, backup, license acceptance or existing service
change occurred during this investigation.
