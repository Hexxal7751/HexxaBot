-- This command is to be executed in SupaBase's SQL editor

-- Function to create per-guild tables
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
    -- Enable RLS and add permissive authenticated policy
    execute format('alter table %I enable row level security', 'rps_stats_' || safe_id);
    begin
        execute format(
            'create policy %I on %I for all to authenticated using (true) with check (true)',
            'rls_auth_all_rps_' || safe_id,
            'rps_stats_' || safe_id
        );
    exception
        when duplicate_object then null;
    end;

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
    execute format('alter table %I enable row level security', 'guess_number_stats_' || safe_id);
    begin
        execute format(
            'create policy %I on %I for all to authenticated using (true) with check (true)',
            'rls_auth_all_guess_' || safe_id,
            'guess_number_stats_' || safe_id
        );
    exception
        when duplicate_object then null;
    end;

    -- TicTacToe table
    execute format(
        'create table if not exists %I (
            user_id text primary key,
            wins integer default 0,
            losses integer default 0,
            draws integer default 0,
            total_games integer default 0
        )', 'tictactoe_stats_' || safe_id);
    execute format('alter table %I enable row level security', 'tictactoe_stats_' || safe_id);
    begin
        execute format(
            'create policy %I on %I for all to authenticated using (true) with check (true)',
            'rls_auth_all_ttt_' || safe_id,
            'tictactoe_stats_' || safe_id
        );
    exception
        when duplicate_object then null;
    end;

    -- Battle table
    execute format(
        'create table if not exists %I (
            user_id text primary key,
            wins integer default 0,
            losses integer default 0,
            total_games integer default 0
        )', 'battle_stats_' || safe_id);
    execute format('alter table %I enable row level security', 'battle_stats_' || safe_id);
    begin
        execute format(
            'create policy %I on %I for all to authenticated using (true) with check (true)',
            'rls_auth_all_battle_' || safe_id,
            'battle_stats_' || safe_id
        );
    exception
        when duplicate_object then null;
    end;

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
    execute format('alter table %I enable row level security', 'flipnfind_stats_' || safe_id);
    begin
        execute format(
            'create policy %I on %I for all to authenticated using (true) with check (true)',
            'rls_auth_all_flip_' || safe_id,
            'flipnfind_stats_' || safe_id
        );
    exception
        when duplicate_object then null;
    end;

    -- Kidnapped Jack table
    execute format(
        'create table if not exists %I (
            user_id text primary key,
            games_played integer default 0,
            escapes integer default 0,
            kidnapper_count integer default 0,
            total_time real default 0,
            best_time real default null,
            best_placement integer default null,
            total_wins integer default 0,
            total_placements integer default 0,
            placement_sum integer default 0
        )', 'kidnapped_jack_stats_' || safe_id);
    execute format('alter table %I enable row level security', 'kidnapped_jack_stats_' || safe_id);
    begin
        execute format(
            'create policy %I on %I for all to authenticated using (true) with check (true)',
            'rls_auth_all_kj_' || safe_id,
            'kidnapped_jack_stats_' || safe_id
        );
    exception
        when duplicate_object then null;
    end;
end;
$$ language plpgsql;
