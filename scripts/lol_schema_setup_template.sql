-- ==========================
-- SECTION 1: CREATE ROLES
-- ==========================
CREATE ROLE admin_role;
CREATE ROLE manager_role;
CREATE ROLE read_only_role;

-- ==========================
-- SECTION 2: CREATE USERS
-- ==========================
CREATE USER admin_user IDENTIFIED BY "{{ADMIN_USER_PASS}}";
CREATE USER manager_user IDENTIFIED BY "{{MANAGER_USER_PASS}}";
CREATE USER regular_user IDENTIFIED BY "{{REGULAR_USER_PASS}}";

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
BEFORE INSERT ON Ban
FOR EACH ROW
DECLARE
v_team_count NUMBER;
    v_game_count NUMBER;
BEGIN
    -- Count how many bans already exist for the same (game_id, team_id)
SELECT COUNT(*) INTO v_team_count
FROM Ban
WHERE game_id = :NEW.game_id
  AND team_id = :NEW.team_id;

IF v_team_count >= 5 THEN
       RAISE_APPLICATION_ERROR(-20001, 'Team Ban Limit Exceeded: A team cannot have more than 5 bans per game.');
END IF;

    -- Count total bans for the entire game (both teams)
SELECT COUNT(*) INTO v_game_count
FROM Ban
WHERE game_id = :NEW.game_id;

IF v_game_count >= 10 THEN
       RAISE_APPLICATION_ERROR(-20002, 'Game Ban Limit Exceeded: Cannot exceed 10 bans per game.');
END IF;
END;
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

-- Manager can read/write (SELECT, INSERT, UPDATE, DELETE) on all tables
GRANT SELECT, INSERT, UPDATE, DELETE ON Player TO manager_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON Team TO manager_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON Game TO manager_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON Champion TO manager_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON PlayerStats TO manager_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TeamStats TO manager_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON Ban TO manager_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON Pick TO manager_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON PlayerDeletionLog TO manager_role;

-- Read-only role can only SELECT from all tables
GRANT SELECT ON Player TO read_only_role;
GRANT SELECT ON Team TO read_only_role;
GRANT SELECT ON Game TO read_only_role;
GRANT SELECT ON Champion TO read_only_role;
GRANT SELECT ON PlayerStats TO read_only_role;
GRANT SELECT ON TeamStats TO read_only_role;
GRANT SELECT ON Ban TO read_only_role;
GRANT SELECT ON Pick TO read_only_role;
GRANT SELECT ON PlayerDeletionLog TO read_only_role;

-- Admin role: full DDL on these objects is already granted above.
GRANT SELECT, INSERT, UPDATE, DELETE ON Player TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON Team TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON Game TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON Champion TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON PlayerStats TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TeamStats TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON Ban TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON Pick TO admin_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON PlayerDeletionLog TO admin_role;

-- ==========================
-- SECTION 8: Final Checks
-- ==========================
-- Show the roles, users, and privileges
PROMPT
PROMPT ========== SETUP COMPLETE ==========
PROMPT Created Roles: admin_role, manager_role, read_only_role
PROMPT Created Users: admin_user, manager_user, regular_user
PROMPT Created Tables: Player, Team, Game, Champion, PlayerStats, TeamStats, Ban, Pick, PlayerDeletionLog
PROMPT Created Triggers: trg_update_team_stats, trg_log_player_deletion, trg_limit_bans, trg_limit_picks
PROMPT Granted Object Privileges to Roles