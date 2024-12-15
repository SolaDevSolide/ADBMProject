import os
import oracledb
import pandas as pd
from dotenv import load_dotenv


def create_connection(username, password, host, port, service):
    try:
        dsn_str = f"{host}:{port}/{service}"
        connection = oracledb.connect(user=username, password=password, dsn=dsn_str)
        print("Connection to Oracle DB successful")
        return connection
    except oracledb.DatabaseError as e:
        print(f"Database connection error: {e}")
        return None


def execute_query(connection, query, params=None):
    cursor = connection.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        connection.commit()
    except oracledb.DatabaseError as e:
        print(f"Error executing query: {e}")
    finally:
        cursor.close()


def remove_duplicates(df, subset):
    return df.drop_duplicates(subset=subset, keep='first')


def merge_player(connection, player_id, player_name, position):
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
    MERGE operation for PlayerStats to handle duplicates.
    """
    sql = """
    MERGE INTO PlayerStats ps
    USING (SELECT :game_id AS game_id, :player_id AS player_id FROM dual) src
    ON (ps.game_id = src.game_id AND ps.player_id = src.player_id)
    WHEN MATCHED THEN
        UPDATE SET 
            team_id = :team_id,
            position = :position,
            champion_id = :champion_id,
            kills = :kills,
            deaths = :deaths,
            assists = :assists,
            gold_earned = :gold_earned,
            cs = :cs
    WHEN NOT MATCHED THEN
        INSERT (game_id, player_id, team_id, position, champion_id, kills, deaths, assists, gold_earned, cs)
        VALUES (:game_id, :player_id, :team_id, :position, :champion_id, :kills, :deaths, :assists, :gold_earned, :cs)
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



def insert_bans_safely(connection, game_id, team_id, ban_cols, row):
    ban_order = 1
    for b_col in ban_cols:
        if ban_order > 5:
            print(f"Skipping additional bans for team {team_id} in game {game_id}: Ban limit reached.")
            break

        ban_champion_name = str(row[b_col]) if row[b_col] else ''
        if ban_champion_name:
            ban_champion_id = ban_champion_name.lower().replace(" ", "_")
            merge_champion(connection, ban_champion_id, ban_champion_name)

            sql = """
            MERGE INTO Ban b
            USING (SELECT :game_id AS game_id, :team_id AS team_id, :ban_order AS ban_order FROM dual) src
            ON (b.game_id = src.game_id AND b.team_id = src.team_id AND b.ban_order = src.ban_order)
            WHEN NOT MATCHED THEN
                INSERT (game_id, team_id, ban_order, champion_id)
                VALUES (:game_id, :team_id, :ban_order, :champion_id)
            """
            params = {
                'game_id': game_id,
                'team_id': team_id,
                'ban_order': ban_order,
                'champion_id': ban_champion_id
            }
            try:
                execute_query(connection, sql, params)
                ban_order += 1
            except oracledb.DatabaseError as e:
                if "ORA-20001" in str(e):
                    print(f"Suppressed error: Team Ban Limit Exceeded for team {team_id} in game {game_id}.")
                else:
                    print(f"Error inserting ban {ban_champion_name} for team {team_id}: {e}")
                continue


def process_df1(connection, df1):
    for _, row in df1.iterrows():
        game_id = row['gameid']
        player_id = row['playerid']
        team_id = row['teamid']

        if not all([game_id, player_id, team_id]):
            print(f"Skipping invalid row in df1: {row}")
            continue

        player_name = str(row['playername']) if row['playername'] else 'Unknown'
        position = str(row['position']) if row['position'] else 'Unknown'
        merge_player(connection, player_id, player_name, position)

        champion_name = str(row['champion']) if row['champion'] else 'Unknown'
        champion_id = champion_name.lower().replace(" ", "_")

        # Ensure the champion exists in the Champion table
        try:
            merge_champion(connection, champion_id, champion_name)
        except oracledb.DatabaseError as e:
            print(f"Error inserting champion: {champion_name}, {e}")
            continue

        kills = int(row['kills']) if str(row['kills']).isdigit() else 0
        deaths = int(row['deaths']) if str(row['deaths']).isdigit() else 0
        assists = int(row['assists']) if str(row['assists']).isdigit() else 0
        cs = int(row['total cs']) if str(row['total cs']).isdigit() else 0
        gold_earned = 0

        try:
            insert_player_stats(connection, game_id, player_id, team_id, position, champion_id, kills, deaths, assists, gold_earned, cs)
        except oracledb.DatabaseError as e:
            print(f"Error inserting player stats: {e}")

        insert_bans_safely(connection, game_id, team_id, ['ban1', 'ban2', 'ban3', 'ban4', 'ban5'], row)


def process_df2(connection, df2):
    for _, row in df2.iterrows():
        game_id = row['gameid']
        t1_id, t2_id = row['t1_id'], row['t2_id']

        if not all([game_id, t1_id, t2_id]):
            print(f"Skipping invalid row in df2: {row}")
            continue

        t1_name = str(row['t1_name']) if row['t1_name'] else 'Unknown'
        t2_name = str(row['t2_name']) if row['t2_name'] else 'Unknown'

        try:
            merge_team(connection, t1_id, t1_name)
            merge_team(connection, t2_id, t2_name)
        except oracledb.DatabaseError as e:
            print(f"Error inserting team data: {e}")


def main():
    load_dotenv()

    host = os.getenv("ORA_HOST")
    port = os.getenv("ORA_PORT")
    service = os.getenv("ORA_SERVICE")
    password = os.getenv("ADMIN_USER_PASS")
    csv1_path = "../" + os.getenv("CSV1")
    csv2_path = "../" + os.getenv("CSV2")

    connection = create_connection("admin_user", password, host, port, service)
    if not connection:
        return

    df1 = pd.read_csv(csv1_path, sep=';')
    df2 = pd.read_csv(csv2_path, sep=';')

    # Define critical columns for df1 and df2
    critical_columns_df1 = ['gameid', 'teamid', 'playerid', 'champion']  # Add all columns you need to process
    critical_columns_df2 = ['gameid', 't1_id', 't2_id']  # Add all columns you need to process

    # Remove rows with NULL values in critical columns for df1
    df1 = df1.dropna(subset=critical_columns_df1)

    # Remove rows with NULL values in critical columns for df2
    df2 = df2.dropna(subset=critical_columns_df2)

    df1 = remove_duplicates(df1, subset=['gameid', 'playerid', 'teamid'])
    df2 = remove_duplicates(df2, subset=['gameid', 't1_id', 't2_id'])

    process_df1(connection, df1)
    process_df2(connection, df2)

    connection.close()
    print("Data import completed successfully.")


if __name__ == "__main__":
    main()