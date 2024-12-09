-- Ensure you're connected to the correct Oracle schema.

-- Table: Player
CREATE TABLE Player (
                        player_id VARCHAR2(50) PRIMARY KEY,
                        player_name VARCHAR2(100) NOT NULL,
                        position VARCHAR2(10) NOT NULL
);

-- Table: Team
CREATE TABLE Team (
                      team_id VARCHAR2(50) PRIMARY KEY,
                      team_name VARCHAR2(100) NOT NULL
);

-- Table: Game
CREATE TABLE Game (
                      game_id VARCHAR2(50) PRIMARY KEY,
                      game_date TIMESTAMP NOT NULL,
                      league VARCHAR2(50),
                      patch VARCHAR2(10)
);

-- Table: Champion
CREATE TABLE Champion (
                          champion_id VARCHAR2(50) PRIMARY KEY,
                          champion_name VARCHAR2(50) NOT NULL
);

-- Table: PlayerStats
CREATE TABLE PlayerStats (
                             game_id VARCHAR2(50) NOT NULL,
                             player_id VARCHAR2(50) NOT NULL,
                             team_id VARCHAR2(50) NOT NULL,
                             position VARCHAR2(10) NOT NULL,
                             champion_id VARCHAR2(50) NOT NULL,
                             kills NUMBER,
                             deaths NUMBER,
                             assists NUMBER,
                             gold_earned NUMBER,
                             cs NUMBER,
                             CONSTRAINT pk_playerstats PRIMARY KEY (game_id, player_id),
                             CONSTRAINT fk_ps_game FOREIGN KEY (game_id) REFERENCES Game(game_id),
                             CONSTRAINT fk_ps_player FOREIGN KEY (player_id) REFERENCES Player(player_id),
                             CONSTRAINT fk_ps_team FOREIGN KEY (team_id) REFERENCES Team(team_id),
                             CONSTRAINT fk_ps_champion FOREIGN KEY (champion_id) REFERENCES Champion(champion_id)
);

-- Table: TeamStats
CREATE TABLE TeamStats (
                           game_id VARCHAR2(50) NOT NULL,
                           team_id VARCHAR2(50) NOT NULL,
                           total_kills NUMBER,
                           total_deaths NUMBER,
                           total_assists NUMBER,
                           CONSTRAINT pk_teamstats PRIMARY KEY (game_id, team_id),
                           CONSTRAINT fk_ts_game FOREIGN KEY (game_id) REFERENCES Game(game_id),
                           CONSTRAINT fk_ts_team FOREIGN KEY (team_id) REFERENCES Team(team_id)
);

-- Table: Ban
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

-- Table: Pick
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
