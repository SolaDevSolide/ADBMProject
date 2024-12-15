-- ==========================
-- SECTION 1: CREATE ROLES
-- ==========================
CREATE ROLE admin_role;
CREATE ROLE manager_role;
CREATE ROLE read_only_role;

-- ==========================
-- SECTION 2: CREATE USERS
-- ==========================
CREATE USER admin_user IDENTIFIED BY "Admin#123";
CREATE USER manager_user IDENTIFIED BY "Manager#123";
CREATE USER regular_user IDENTIFIED BY "Regular#123";

-- Grant CONNECT so the users can log in
GRANT CONNECT TO admin_user;
GRANT CONNECT TO manager_user;
GRANT CONNECT TO regular_user;

-- ==========================
-- SECTION 3: ASSIGN PRIVILEGES TO ROLES
-- ==========================
-- admin_role: Full DDL privileges + resource management
GRANT CREATE SESSION, CREATE TABLE, CREATE VIEW, CREATE ANY TRIGGER, CREATE ANY PROCEDURE,
      ALTER ANY TABLE, DROP ANY TABLE, CREATE ANY SEQUENCE, CREATE ANY MATERIALIZED VIEW
TO admin_role;

-- manager_role: DML privileges (select, insert, update, delete)
-- We'll grant object-level privileges after tables are created
GRANT CREATE SESSION TO manager_role;

-- read_only_role: SELECT only
GRANT CREATE SESSION TO read_only_role;

-- ==========================
-- SECTION 4: GRANT ROLES TO USERS
-- ==========================
GRANT admin_role TO admin_user;
-- The admin_user will have all privileges from admin_role

-- The manager_user will get manager_role by default;
-- Additional object privileges to be granted after tables are created.
GRANT manager_role TO manager_user;

-- The regular_user will get read_only_role (SELECT only)
GRANT read_only_role TO regular_user;

-- ==========================
-- SECTION 5: CREATE TABLES
-- ==========================
-- If you face ORA-65096 in PDB:
-- ALTER SESSION SET "_ORACLE_SCRIPT"=true;
ALTER SESSION SET CURRENT_SCHEMA = admin_user;

-- Drop existing tables if they exist
DECLARE
    v_table_exists NUMBER;
BEGIN
    FOR t IN (
        SELECT table_name
        FROM user_tables
        WHERE table_name IN ('PLAYER', 'TEAM', 'GAME', 'CHAMPION', 'PLAYERSTATS', 'TEAMSTATS', 'BAN', 'PICK', 'PLAYERDELETIONLOG')
        ) LOOP
            EXECUTE IMMEDIATE 'DROP TABLE ' || t.table_name || ' CASCADE CONSTRAINTS';
        END LOOP;
END;
/


-- TABLE: Player
CREATE TABLE Player (
                        player_id VARCHAR2(50) PRIMARY KEY,
                        player_name VARCHAR2(100) NOT NULL,
                        position VARCHAR2(10) NOT NULL
);

-- TABLE: Team
CREATE TABLE Team (
                      team_id VARCHAR2(50) PRIMARY KEY,
                      team_name VARCHAR2(100) NOT NULL
);

-- TABLE: Game
CREATE TABLE Game (
                      game_id VARCHAR2(50) PRIMARY KEY,
                      game_date TIMESTAMP NOT NULL,
                      league VARCHAR2(50),
                      patch VARCHAR2(10)
);

-- TABLE: Champion
CREATE TABLE Champion (
                          champion_id VARCHAR2(50) PRIMARY KEY,
                          champion_name VARCHAR2(50) NOT NULL
);

-- TABLE: PlayerStats
CREATE TABLE PlayerStats (
                             game_id VARCHAR2(50) NOT NULL,
                             player_id VARCHAR2(50) NOT NULL,
                             team_id VARCHAR2(50) NOT NULL,
                             position VARCHAR2(10) NOT NULL,
                             champion_id VARCHAR2(50) NOT NULL,
                             kills NUMBER DEFAULT 0,
                             deaths NUMBER DEFAULT 0,
                             assists NUMBER DEFAULT 0,
                             gold_earned NUMBER DEFAULT 0,
                             cs NUMBER DEFAULT 0,
                             CONSTRAINT pk_playerstats PRIMARY KEY (game_id, player_id),
                             CONSTRAINT fk_ps_game FOREIGN KEY (game_id) REFERENCES Game(game_id),
                             CONSTRAINT fk_ps_player FOREIGN KEY (player_id) REFERENCES Player(player_id),
                             CONSTRAINT fk_ps_team FOREIGN KEY (team_id) REFERENCES Team(team_id),
                             CONSTRAINT fk_ps_champion FOREIGN KEY (champion_id) REFERENCES Champion(champion_id)
);

-- TABLE: TeamStats
CREATE TABLE TeamStats (
                           game_id VARCHAR2(50) NOT NULL,
                           team_id VARCHAR2(50) NOT NULL,
                           total_kills NUMBER DEFAULT 0,
                           total_deaths NUMBER DEFAULT 0,
                           total_assists NUMBER DEFAULT 0,
                           CONSTRAINT pk_teamstats PRIMARY KEY (game_id, team_id),
                           CONSTRAINT fk_ts_game FOREIGN KEY (game_id) REFERENCES Game(game_id),
                           CONSTRAINT fk_ts_team FOREIGN KEY (team_id) REFERENCES Team(team_id)
);

-- TABLE: Ban
CREATE TABLE Ban (
                     game_id VARCHAR2(50) NOT NULL,
                     team_id VARCHAR2(50) NOT NULL,
                     ban_order NUMBER NOT NULL,
                     champion_id VARCHAR2(50) NOT NULL,
                     CONSTRAINT pk_ban PRIMARY KEY (game_id, team_id, ban_order),
                     CONSTRAINT fk_ban_game FOREIGN KEY (game_id) REFERENCES Game(game_id),
                     CONSTRAINT fk_ban_team FOREIGN KEY (team_id) REFERENCES Team(team_id),
                     CONSTRAINT fk_ban_champion FOREIGN KEY (champion_id) REFERENCES Champion(champion_id)
);

-- TABLE: Pick
CREATE TABLE Pick (
                      game_id VARCHAR2(50) NOT NULL,
                      team_id VARCHAR2(50) NOT NULL,
                      pick_order NUMBER NOT NULL,
                      player_id VARCHAR2(50) NOT NULL,
                      champion_id VARCHAR2(50) NOT NULL,
                      CONSTRAINT pk_pick PRIMARY KEY (game_id, team_id, pick_order),
                      CONSTRAINT fk_pick_game FOREIGN KEY (game_id) REFERENCES Game(game_id),
                      CONSTRAINT fk_pick_team FOREIGN KEY (team_id) REFERENCES Team(team_id),
                      CONSTRAINT fk_pick_player FOREIGN KEY (player_id) REFERENCES Player(player_id),
                      CONSTRAINT fk_pick_champion FOREIGN KEY (champion_id) REFERENCES Champion(champion_id)
);

-- ==========================
-- SECTION 6: CREATE TRIGGERS
-- ==========================

-- TRIGGER #1: After inserting player stats, update the TeamStats table.
--    If a new row is inserted in PlayerStats, add kills/deaths/assists
--    to the existing row in TeamStats for the same game/team.

CREATE OR REPLACE TRIGGER trg_update_team_stats
AFTER INSERT ON PlayerStats
FOR EACH ROW
BEGIN
UPDATE TeamStats
SET total_kills = total_kills + :NEW.kills,
    total_deaths = total_deaths + :NEW.deaths,
    total_assists = total_assists + :NEW.assists
WHERE game_id = :NEW.game_id
  AND team_id = :NEW.team_id;
END;
/

-- TRIGGER #2: Log deletions from the Player table to a separate log table

-- First create a log table:
CREATE TABLE PlayerDeletionLog (
                                   deleted_player_id VARCHAR2(50),
                                   deletion_timestamp TIMESTAMP DEFAULT SYSTIMESTAMP
);

CREATE OR REPLACE TRIGGER trg_log_player_deletion
BEFORE DELETE ON Player
FOR EACH ROW
BEGIN
INSERT INTO PlayerDeletionLog (deleted_player_id)
VALUES (:OLD.player_id);
END;
/

------------------------------------------------------------------------------
-- Enforcing UML Cardinalities for BAN (Team can have 0..5 bans, Game can have up to 10 bans)
------------------------------------------------------------------------------

CREATE OR REPLACE TRIGGER trg_limit_bans
    FOR INSERT ON Ban
    COMPOUND TRIGGER

    /* A local in-memory collection to hold the new row IDs for this statement */
    TYPE ban_key IS RECORD (game_id VARCHAR2(50), team_id VARCHAR2(50));
    TYPE ban_array IS TABLE OF ban_key INDEX BY PLS_INTEGER;

    g_ban_data ban_array;
    idx PLS_INTEGER := 0;

BEFORE EACH ROW IS
BEGIN
    /* Collect (game_id, team_id) for checking later in AFTER STATEMENT */
    idx := idx + 1;
    g_ban_data(idx).game_id := :NEW.game_id;
    g_ban_data(idx).team_id := :NEW.team_id;
END BEFORE EACH ROW;

    AFTER STATEMENT IS
        v_team_count NUMBER;
        v_game_count NUMBER;
    BEGIN
        /* We iterate over collected data, grouping them to check constraints only once per (game_id, team_id). */
        DECLARE
            TYPE pair_rec IS RECORD (game_id VARCHAR2(50), team_id VARCHAR2(50));
            TYPE pair_table IS TABLE OF pair_rec;
            unique_pairs pair_table := pair_table();
        BEGIN
            /* Collect unique (game_id, team_id) pairs from g_ban_data */
            FOR i IN 1..idx LOOP
                -- If not already in unique_pairs, add it
                    unique_pairs.EXTEND;
                    unique_pairs(unique_pairs.LAST).game_id := g_ban_data(i).game_id;
                    unique_pairs(unique_pairs.LAST).team_id := g_ban_data(i).team_id;
                END LOOP;

            FOR i2 IN 1..unique_pairs.COUNT LOOP
                    SELECT COUNT(*) INTO v_team_count
                    FROM Ban
                    WHERE game_id = unique_pairs(i2).game_id
                      AND team_id = unique_pairs(i2).team_id;

                    IF v_team_count > 5 THEN
                        RAISE_APPLICATION_ERROR(-20001,
                                                'Team Ban Limit Exceeded: A team cannot have more than 5 bans per game.');
                    END IF;

                    SELECT COUNT(*) INTO v_game_count
                    FROM Ban
                    WHERE game_id = unique_pairs(i2).game_id;

                    IF v_game_count > 10 THEN
                        RAISE_APPLICATION_ERROR(-20002,
                                                'Game Ban Limit Exceeded: Cannot exceed 10 bans per game.');
                    END IF;
                END LOOP;
        END;
    END AFTER STATEMENT;

    END trg_limit_bans;
/


------------------------------------------------------------------------------
-- Enforcing UML Cardinalities for PICK (Team must have exactly 5 picks, Game total 10 picks)
------------------------------------------------------------------------------

CREATE OR REPLACE TRIGGER trg_limit_picks
BEFORE INSERT ON Pick
FOR EACH ROW
DECLARE
v_team_picks  NUMBER;
    v_game_picks  NUMBER;
BEGIN
    -- Count how many picks already exist for the same (game_id, team_id)
SELECT COUNT(*) INTO v_team_picks
FROM Pick
WHERE game_id = :NEW.game_id
  AND team_id = :NEW.team_id;

IF v_team_picks >= 5 THEN
       RAISE_APPLICATION_ERROR(-20003, 'Team Pick Limit Exceeded: A team cannot have more than 5 picks per game.');
END IF;

    -- Count total picks for the entire game
SELECT COUNT(*) INTO v_game_picks
FROM Pick
WHERE game_id = :NEW.game_id;

IF v_game_picks >= 10 THEN
       RAISE_APPLICATION_ERROR(-20004, 'Game Pick Limit Exceeded: Cannot exceed 10 picks per game.');
END IF;
END;
/

-- ==========================
-- SECTION 7: GRANT OBJECT PRIVILEGES
-- ==========================
-- Now that the tables are created, we grant privileges to roles.

-- Manager Role: Full DML privileges (SELECT, INSERT, UPDATE, DELETE) on all tables
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_user.Player TO manager_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_user.Team TO manager_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_user.Game TO manager_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_user.Champion TO manager_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_user.PlayerStats TO manager_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_user.TeamStats TO manager_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_user.Ban TO manager_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_user.Pick TO manager_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_user.PlayerDeletionLog TO manager_role;

-- Read-Only Role: SELECT privileges only on all tables
GRANT SELECT ON admin_user.Player TO read_only_role;
GRANT SELECT ON admin_user.Team TO read_only_role;
GRANT SELECT ON admin_user.Game TO read_only_role;
GRANT SELECT ON admin_user.Champion TO read_only_role;
GRANT SELECT ON admin_user.PlayerStats TO read_only_role;
GRANT SELECT ON admin_user.TeamStats TO read_only_role;
GRANT SELECT ON admin_user.Ban TO read_only_role;
GRANT SELECT ON admin_user.Pick TO read_only_role;
GRANT SELECT ON admin_user.PlayerDeletionLog TO read_only_role;

-- Admin Role: Full DML privileges on all tables
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_user.Player TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_user.Team TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_user.Game TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_user.Champion TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_user.PlayerStats TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_user.TeamStats TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_user.Ban TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_user.Pick TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_user.PlayerDeletionLog TO admin_role;


-- ==========================
-- SECTION 8: CREATE SYNONYMS
-- ==========================
-- Create public synonyms for easier access to tables
CREATE OR REPLACE PUBLIC SYNONYM Player FOR admin_user.Player;
CREATE OR REPLACE PUBLIC SYNONYM Team FOR admin_user.Team;
CREATE OR REPLACE PUBLIC SYNONYM Game FOR admin_user.Game;
CREATE OR REPLACE PUBLIC SYNONYM Champion FOR admin_user.Champion;
CREATE OR REPLACE PUBLIC SYNONYM PlayerStats FOR admin_user.PlayerStats;
CREATE OR REPLACE PUBLIC SYNONYM TeamStats FOR admin_user.TeamStats;
CREATE OR REPLACE PUBLIC SYNONYM Ban FOR admin_user.Ban;
CREATE OR REPLACE PUBLIC SYNONYM Pick FOR admin_user.Pick;
CREATE OR REPLACE PUBLIC SYNONYM PlayerDeletionLog FOR admin_user.PlayerDeletionLog;

-- ==========================
-- SECTION 9: Final Checks
-- ==========================
-- Show the roles, users, and privileges
PROMPT
PROMPT ========== SETUP COMPLETE ==========
PROMPT Created Roles: admin_role, manager_role, read_only_role
PROMPT Created Users: admin_user, manager_user, regular_user
PROMPT Created Tables: Player, Team, Game, Champion, PlayerStats, TeamStats, Ban, Pick, PlayerDeletionLog
PROMPT Created Triggers: trg_update_team_stats, trg_log_player_deletion, trg_limit_bans, trg_limit_picks
PROMPT Granted Object Privileges to Roles
PROMPT Created Public Synonyms: Player, Team, Game, Champion, PlayerStats, TeamStats, Ban, Pick, PlayerDeletionLog
EXIT;
