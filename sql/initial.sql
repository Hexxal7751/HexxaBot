-- This code is served into Supabase's SQL Editor

create or replace function create_guild_tables(guild_id text)
returns void as $$
declare
    safe_id text := regexp_replace(guild_id, '[^0-9]', '', 'g');
begin
    -- RPS table
    execute format(
        'create table if not exists %I (
            user_id text primary key,
            wins integer default 0,
            losses integer default 0,
            ties integer default 0,
            total_games integer default 0
        )', 'rps_stats_' || safe_id);

    -- Guess Number table
    execute format(
        'create table if not exists %I (
            user_id text primary key,
            correct_guesses integer default 0,
            incorrect_guesses integer default 0,
            total_games integer default 0,
            guesses jsonb default ''[]'',
            guess_gaps jsonb default ''[]''
        )', 'guess_number_stats_' || safe_id);

    -- TicTacToe table
    execute format(
        'create table if not exists %I (
            user_id text primary key,
            wins integer default 0,
            losses integer default 0,
            draws integer default 0,
            total_games integer default 0
        )', 'tictactoe_stats_' || safe_id);

    -- Battle table
    execute format(
        'create table if not exists %I (
            user_id text primary key,
            wins integer default 0,
            losses integer default 0,
            total_games integer default 0
        )', 'battle_stats_' || safe_id);

    -- Flip & Find table
    execute format(
        'create table if not exists %I (
            user_id text primary key,
            wins integer default 0,
            losses integer default 0,
            total_games integer default 0,
            best_time real default null,
            best_turns integer default null,
            total_turns integer default 0,
            total_time real default 0,
            star_cards integer default 0
        )', 'flipnfind_stats_' || safe_id);
end;
$$ language plpgsql;
