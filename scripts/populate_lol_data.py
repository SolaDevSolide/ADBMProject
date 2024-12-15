import os

import cx_Oracle
import pandas as pd
from dotenv import load_dotenv


def create_connection(username, password, host, port, service):
    """
    Creates a connection to Oracle using cx_Oracle.
    DSN is built from host, port, service name.
    """
    try:
        dsn_str = f"{host}:{port}/{service}"
        connection = cx_Oracle.connect(user=username, password=password, dsn=dsn_str)
        print("Connection to Oracle DB successful")
        return connection
    except cx_Oracle.DatabaseError as e:
        print(f"Database connection error: {e}")
        return None

def execute_query(connection, query, params=None):
    """
    Executes a single SQL query or DML statement with optional parameters.
    Commits after success.
    """
    cursor = connection.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        connection.commit()
    except cx_Oracle.DatabaseError as e:
        print(f"Error executing query: {e}")
    finally:
        cursor.close()

def merge_player(connection, player_id, player_name, position):
    """
    MERGE operation for Player, ensuring upsert behavior by player_id.
    """
    sql = """
    MERGE INTO Player p
    USING (SELECT :player_id AS player_id FROM dual) d
    ON (p.player_id = d.player_id)
    WHEN MATCHED THEN
        UPDATE SET player_name = :player_name, position = :position
    WHEN NOT MATCHED THEN
        INSERT (player_id, player_name, position)
        VALUES (:player_id, :player_name, :position)
    """
    params = {'player_id': player_id, 'player_name': player_name, 'position': position}
    execute_query(connection, sql, params)

def merge_team(connection, team_id, team_name):
    """
    MERGE operation for Team, upserting by team_id.
    """
    sql = """
    MERGE INTO Team t
    USING (SELECT :team_id AS team_id FROM dual) d
    ON (t.team_id = d.team_id)
    WHEN MATCHED THEN
        UPDATE SET team_name = :team_name
    WHEN NOT MATCHED THEN
        INSERT (team_id, team_name)
        VALUES (:team_id, :team_name)
    """
    params = {'team_id': team_id, 'team_name': team_name}
    execute_query(connection, sql, params)

def merge_game(connection, game_id, game_date, league, patch):
    """
    MERGE operation for Game, upserting by game_id.
    """
    sql = """
    MERGE INTO Game g
    USING (SELECT :game_id AS game_id FROM dual) d
    ON (g.game_id = d.game_id)
    WHEN MATCHED THEN
        UPDATE SET game_date = :game_date, league = :league, patch = :patch
    WHEN NOT MATCHED THEN
        INSERT (game_id, game_date, league, patch)
        VALUES (:game_id, :game_date, :league, :patch)
    """
    params = {'game_id': game_id, 'game_date': game_date, 'league': league, 'patch': patch}
    execute_query(connection, sql, params)

def merge_champion(connection, champion_id, champion_name):
    """
    MERGE operation for Champion, upserting by champion_id.
    """
    sql = """
    MERGE INTO Champion c
    USING (SELECT :champion_id AS champion_id FROM dual) d
    ON (c.champion_id = d.champion_id)
    WHEN MATCHED THEN
        UPDATE SET champion_name = :champion_name
    WHEN NOT MATCHED THEN
        INSERT (champion_id, champion_name)
        VALUES (:champion_id, :champion_name)
    """
    params = {'champion_id': champion_id, 'champion_name': champion_name}
    execute_query(connection, sql, params)

def insert_player_stats(connection, game_id, player_id, team_id, position, champion_id, kills, deaths, assists, gold_earned, cs):
    """
    Inserts a record into PlayerStats (unique key: game_id + player_id).
    """
    sql = """
    INSERT INTO PlayerStats 
    (game_id, player_id, team_id, position, champion_id, kills, deaths, assists, gold_earned, cs)
    VALUES 
    (:game_id, :player_id, :team_id, :position, :champion_id, :kills, :deaths, :assists, :gold_earned, :cs)
    """
    params = {
        'game_id': game_id,
        'player_id': player_id,
        'team_id': team_id,
        'position': position,
        'champion_id': champion_id,
        'kills': kills,
        'deaths': deaths,
        'assists': assists,
        'gold_earned': gold_earned,
        'cs': cs
    }
    execute_query(connection, sql, params)

def insert_team_stats(connection, game_id, team_id, total_kills, total_deaths, total_assists):
    """
    Inserts a record into TeamStats (unique key: game_id + team_id).
    """
    sql = """
    INSERT INTO TeamStats (game_id, team_id, total_kills, total_deaths, total_assists)
    VALUES (:game_id, :team_id, :total_kills, :total_deaths, :total_assists)
    """
    params = {
        'game_id': game_id,
        'team_id': team_id,
        'total_kills': total_kills,
        'total_deaths': total_deaths,
        'total_assists': total_assists
    }
    execute_query(connection, sql, params)

def insert_ban(connection, game_id, team_id, ban_order, champion_id):
    """
    Inserts a row into Ban (primary key: game_id + team_id + ban_order).
    """
    sql = """
    INSERT INTO Ban (game_id, team_id, ban_order, champion_id)
    VALUES (:game_id, :team_id, :ban_order, :champion_id)
    """
    params = {
        'game_id': game_id,
        'team_id': team_id,
        'ban_order': ban_order,
        'champion_id': champion_id
    }
    execute_query(connection, sql, params)

def insert_pick(connection, game_id, team_id, pick_order, player_id, champion_id):
    """
    Inserts a row into Pick (primary key: game_id + team_id + pick_order).
    """
    sql = """
    INSERT INTO Pick (game_id, team_id, pick_order, player_id, champion_id)
    VALUES (:game_id, :team_id, :pick_order, :player_id, :champion_id)
    """
    params = {
        'game_id': game_id,
        'team_id': team_id,
        'pick_order': pick_order,
        'player_id': player_id,
        'champion_id': champion_id
    }
    execute_query(connection, sql, params)

def main():
    # Load environment variables from .env
    load_dotenv()

    host = os.getenv("ORA_HOST")
    port = os.getenv("ORA_PORT")
    service = os.getenv("ORA_SERVICE")
    username = os.getenv("ORA_USERNAME")
    password = os.getenv("ORA_PASSWORD")

    csv1_path = os.getenv("CSV1")
    csv2_path = os.getenv("CSV2")
    xls1_path = os.getenv("XLS1")

    connection = create_connection(username, password, host, port, service)
    if not connection:
        return

    df1 = pd.read_csv(csv1_path, sep=';')
    df2 = pd.read_csv(csv2_path, sep=';')
    df3 = pd.read_excel(xls1_path)

    df1.fillna('', inplace=True)
    df2.fillna('', inplace=True)
    df3.fillna('', inplace=True)

    # Populate from df1 (participant-level CSV)
    for _, row in df1.iterrows():
        game_id = row['gameid']
        date_str = row['date']
        league = row['league']
        patch = row['patch']
        try:
            game_date = pd.to_datetime(date_str)
        except:
            game_date = None

        merge_game(connection, game_id, game_date, league, patch)

        player_id = str(row['playerid']) if row['playerid'] else ''
        player_name = str(row['playername']) if row['playername'] else 'Unknown'
        position = str(row['position']) if row['position'] else 'Unknown'
        merge_player(connection, player_id, player_name, position)

        team_id = str(row['teamid']) if row['teamid'] else ''
        team_name = str(row['teamname']) if row['teamname'] else 'Unknown'
        merge_team(connection, team_id, team_name)

        champion_name = str(row['champion']) if row['champion'] else 'Unknown'
        champion_id = champion_name.lower().replace(" ", "_")
        merge_champion(connection, champion_id, champion_name)

        kills = int(row['kills']) if str(row['kills']).isdigit() else 0
        deaths = int(row['deaths']) if str(row['deaths']).isdigit() else 0
        assists = int(row['assists']) if str(row['assists']).isdigit() else 0
        cs = int(row['cs']) if str(row['cs']).isdigit() else 0

        # There's no direct gold_earned col in df1, using damagetochampions as dummy
        gold_earned = 0
        if 'damagetochampions' in df1.columns and str(row['damagetochampions']).isdigit():
            gold_earned = int(row['damagetochampions'])

        insert_player_stats(connection, game_id, player_id, team_id, position, champion_id,
                            kills, deaths, assists, gold_earned, cs)

        ban_cols = ['ban1','ban2','ban3','ban4','ban5']
        ban_order = 1
        for b_col in ban_cols:
            ban_champion_name = str(row[b_col]) if row[b_col] else ''
            if ban_champion_name:
                ban_champion_id = ban_champion_name.lower().replace(" ", "_")
                merge_champion(connection, ban_champion_id, ban_champion_name)
                insert_ban(connection, game_id, team_id, ban_order, ban_champion_id)
            ban_order += 1

    # Populate from df2 (game-level CSV)
    for _, row in df2.iterrows():
        game_id = row['gameid']
        date_str = row['date']
        league = row['league']
        patch = row['patch']
        try:
            game_date = pd.to_datetime(date_str)
        except:
            game_date = None

        merge_game(connection, game_id, game_date, league, patch)

        # Team 1
        t1_id = str(row['t1_id']) if row['t1_id'] else ''
        t1_name = str(row['t1_name']) if row['t1_name'] else 'Unknown'
        merge_team(connection, t1_id, t1_name)
        t1_kills = int(row['t1_kills']) if str(row['t1_kills']).isdigit() else 0
        t1_deaths = int(row['t1_deaths']) if str(row['t1_deaths']).isdigit() else 0
        t1_assists = 0
        insert_team_stats(connection, game_id, t1_id, t1_kills, t1_deaths, t1_assists)

        t1_ban_cols = ['t1_ban1','t1_ban2','t1_ban3','t1_ban4','t1_ban5']
        ban_order = 1
        for col in t1_ban_cols:
            ban_champion_name = str(row[col]) if row[col] else ''
            if ban_champion_name:
                ban_champion_id = ban_champion_name.lower().replace(" ", "_")
                merge_champion(connection, ban_champion_id, ban_champion_name)
                insert_ban(connection, game_id, t1_id, ban_order, ban_champion_id)
            ban_order += 1

        # Team 2
        t2_id = str(row['t2_id']) if row['t2_id'] else ''
        t2_name = str(row['t2_name']) if row['t2_name'] else 'Unknown'
        merge_team(connection, t2_id, t2_name)
        t2_kills = int(row['t2_kills']) if str(row['t2_kills']).isdigit() else 0
        t2_deaths = int(row['t2_deaths']) if str(row['t2_deaths']).isdigit() else 0
        t2_assists = 0
        insert_team_stats(connection, game_id, t2_id, t2_kills, t2_deaths, t2_assists)

        t2_ban_cols = ['t2_ban1','t2_ban2','t2_ban3','t2_ban4','t2_ban5']
        ban_order = 1
        for col in t2_ban_cols:
            ban_champion_name = str(row[col]) if row[col] else ''
            if ban_champion_name:
                ban_champion_id = ban_champion_name.lower().replace(" ", "_")
                merge_champion(connection, ban_champion_id, ban_champion_name)
                insert_ban(connection, game_id, t2_id, ban_order, ban_champion_id)
            ban_order += 1

        # Team 1 picks
        pick_order = 1
        for i in range(1,6):
            champ_col = f"t1p{i}_champion"
            player_col = f"t1p{i}_playerid"
            pos_col = f"t1p{i}_position"
            champion_name = str(row[champ_col]) if row[champ_col] else ''
            player_id = str(row[player_col]) if row[player_col] else ''
            player_position = str(row[pos_col]) if row[pos_col] else 'Unknown'
            if champion_name and player_id:
                champion_id = champion_name.lower().replace(" ", "_")
                merge_champion(connection, champion_id, champion_name)
                merge_player(connection, player_id, "Unknown", player_position)
                insert_pick(connection, game_id, t1_id, pick_order, player_id, champion_id)
            pick_order += 1

        # Team 2 picks
        pick_order = 1
        for i in range(1,6):
            champ_col = f"t2p{i}_champion"
            player_col = f"t2p{i}_playerid"
            pos_col = f"t2p{i}_position"
            champion_name = str(row[champ_col]) if row[champ_col] else ''
            player_id = str(row[player_col]) if row[player_col] else ''
            player_position = str(row[pos_col]) if row[pos_col] else 'Unknown'
            if champion_name and player_id:
                champion_id = champion_name.lower().replace(" ", "_")
                merge_champion(connection, champion_id, champion_name)
                merge_player(connection, player_id, "Unknown", player_position)
                insert_pick(connection, game_id, t2_id, pick_order, player_id, champion_id)
            pick_order += 1

    # Populate from df3 (Excel) with the same approach if columns match df2
    for _, row in df3.iterrows():
        game_id = row['gameid']
        date_str = row['date']
        league = row['league']
        patch = row['patch']
        try:
            game_date = pd.to_datetime(date_str)
        except:
            game_date = None

        merge_game(connection, game_id, game_date, league, patch)

        # Team 1
        t1_id = str(row['t1_id']) if row['t1_id'] else ''
        t1_name = str(row['t1_name']) if row['t1_name'] else 'Unknown'
        merge_team(connection, t1_id, t1_name)

        t1_kills = int(row['t1_kills']) if str(row['t1_kills']).isdigit() else 0
        t1_deaths = int(row['t1_deaths']) if str(row['t1_deaths']).isdigit() else 0
        t1_assists = 0
        insert_team_stats(connection, game_id, t1_id, t1_kills, t1_deaths, t1_assists)

        t1_ban_cols = ['t1_ban1','t1_ban2','t1_ban3','t1_ban4','t1_ban5']
        ban_order = 1
        for col in t1_ban_cols:
            ban_champion_name = str(row[col]) if row[col] else ''
            if ban_champion_name:
                ban_champion_id = ban_champion_name.lower().replace(" ", "_")
                merge_champion(connection, ban_champion_id, ban_champion_name)
                insert_ban(connection, game_id, t1_id, ban_order, ban_champion_id)
            ban_order += 1

        # Team 2
        t2_id = str(row['t2_id']) if row['t2_id'] else ''
        t2_name = str(row['t2_name']) if row['t2_name'] else 'Unknown'
        merge_team(connection, t2_id, t2_name)

        t2_kills = int(row['t2_kills']) if str(row['t2_kills']).isdigit() else 0
        t2_deaths = int(row['t2_deaths']) if str(row['t2_deaths']).isdigit() else 0
        t2_assists = 0
        insert_team_stats(connection, game_id, t2_id, t2_kills, t2_deaths, t2_assists)

        t2_ban_cols = ['t2_ban1','t2_ban2','t2_ban3','t2_ban4','t2_ban5']
        ban_order = 1
        for col in t2_ban_cols:
            ban_champion_name = str(row[col]) if row[col] else ''
            if ban_champion_name:
                ban_champion_id = ban_champion_name.lower().replace(" ", "_")
                merge_champion(connection, ban_champion_id, ban_champion_name)
                insert_ban(connection, game_id, t2_id, ban_order, ban_champion_id)
            ban_order += 1

        # Team 1 picks in df3
        pick_order = 1
        for i in range(1,6):
            champ_col = f"t1p{i}_champion"
            player_col = f"t1p{i}_playerid"
            pos_col = f"t1p{i}_position"
            champion_name = str(row[champ_col]) if row[champ_col] else ''
            player_id = str(row[player_col]) if row[player_col] else ''
            player_position = str(row[pos_col]) if row[pos_col] else 'Unknown'
            if champion_name and player_id:
                champion_id = champion_name.lower().replace(" ", "_")
                merge_champion(connection, champion_id, champion_name)
                merge_player(connection, player_id, "Unknown", player_position)
                insert_pick(connection, game_id, t1_id, pick_order, player_id, champion_id)
            pick_order += 1

        # Team 2 picks in df3
        pick_order = 1
        for i in range(1,6):
            champ_col = f"t2p{i}_champion"
            player_col = f"t2p{i}_playerid"
            pos_col = f"t2p{i}_position"
            champion_name = str(row[champ_col]) if row[champ_col] else ''
            player_id = str(row[player_col]) if row[player_col] else ''
            player_position = str(row[pos_col]) if row[pos_col] else 'Unknown'
            if champion_name and player_id:
                champion_id = champion_name.lower().replace(" ", "_")
                merge_champion(connection, champion_id, champion_name)
                merge_player(connection, player_id, "Unknown", player_position)
                insert_pick(connection, game_id, t2_id, pick_order, player_id, champion_id)
            pick_order += 1

    connection.close()
    print("Data import completed successfully.")

if __name__ == "__main__":
    main()