-- Fail atomically if historical links cross stable entries.
CREATE TEMP TABLE supersession_check (valid INTEGER CHECK(valid = 1));
INSERT INTO supersession_check
    SELECT 0 FROM match_decision child JOIN match_decision parent ON parent.id = child.supersedes
    WHERE child.entry_id != parent.entry_id LIMIT 1;
DROP TABLE supersession_check;

CREATE TRIGGER match_supersedes_insert BEFORE INSERT ON match_decision
WHEN NEW.supersedes IS NOT NULL AND EXISTS (
    SELECT 1 FROM match_decision WHERE id = NEW.supersedes AND entry_id != NEW.entry_id
)
BEGIN SELECT RAISE(ABORT, 'superseded decision belongs to another entry'); END;

CREATE TRIGGER match_supersedes_update BEFORE UPDATE OF entry_id, supersedes ON match_decision
WHEN EXISTS (
    SELECT 1 FROM match_decision WHERE id = NEW.supersedes AND entry_id != NEW.entry_id
) OR EXISTS (
    SELECT 1 FROM match_decision WHERE supersedes = OLD.id AND entry_id != NEW.entry_id
)
BEGIN SELECT RAISE(ABORT, 'superseded decision belongs to another entry'); END;
