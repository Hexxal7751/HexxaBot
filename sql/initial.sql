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

    -- Roulette stats table (per guild)
    execute format(
        'create table if not exists %I (
            user_id text primary key,
            games_played integer default 0,
            games_won integer default 0,
            games_lost integer default 0,
            total_bet integer default 0,
            total_won integer default 0,
            total_lost integer default 0,
            biggest_win integer default 0,
            biggest_loss integer default 0,
            created_at timestamp with time zone default now(),
            updated_at timestamp with time zone default now()
        )', 'roulette_stats_' || safe_id);
    execute format('alter table %I enable row level security', 'roulette_stats_' || safe_id);
    begin
        execute format(
            'create policy %I on %I for all to authenticated using (true) with check (true)',
            'rls_auth_all_roulette_' || safe_id,
            'roulette_stats_' || safe_id
        );
    exception
        when duplicate_object then null;
    end;
end;
$$ language plpgsql;

-- Economy table (bot-wide, not guild-specific)
create table if not exists economy (
    user_id text primary key,
    balance integer default 1000,
    total_earned integer default 1000,
    total_spent integer default 0,
    last_daily timestamp with time zone default null,
    created_at timestamp with time zone default now(),
    updated_at timestamp with time zone default now()
);

-- Enable RLS and add permissive authenticated policy for economy
alter table economy enable row level security;

-- Create policy for economy table (allow all operations for authenticated users)
do $$
begin
    if not exists (
        select 1 from pg_policies 
        where schemaname = 'public' 
        and tablename = 'economy' 
        and policyname = 'rls_auth_all_economy'
    ) then
        create policy rls_auth_all_economy on economy 
        for all to authenticated 
        using (true) 
        with check (true);
    end if;
end $$;

-- Create social table for tracking daily/monthly/yearly rewards (global, not guild-specific)
create table if not exists social (
    id bigserial primary key,
    user_id text not null unique,
    last_daily timestamp with time zone,
    last_monthly timestamp with time zone,
    last_yearly timestamp with time zone,
    daily_streak integer default 0,
    monthly_streak integer default 0,
    yearly_streak integer default 0,
    total_daily_claimed integer default 0,
    total_monthly_claimed integer default 0,
    total_yearly_claimed integer default 0,
    created_at timestamp with time zone default now(),
    updated_at timestamp with time zone default now()
);

-- Enable RLS on social table
alter table social enable row level security;

-- Create policy for social table (allow all operations for authenticated users)
do $$
begin
    if not exists (
        select 1 from pg_policies 
        where schemaname = 'public' 
        and tablename = 'social' 
        and policyname = 'rls_auth_all_social'
    ) then
        create policy rls_auth_all_social on social 
        for all to authenticated 
        using (true) 
        with check (true);
    end if;
end $$;

-- Create jobs table for tracking user employment (bot-wide, not guild-specific)
create table if not exists jobs (
    id bigserial primary key,
    user_id text not null unique,
    current_job text default null,
    experience integer default 0,
    last_work timestamp with time zone default null,
    work_count integer default 0,
    grace_period_start timestamp with time zone default null,
    total_earned integer default 0,
    created_at timestamp with time zone default now(),
    updated_at timestamp with time zone default now()
);

-- Enable RLS on jobs table
alter table jobs enable row level security;

-- Create policy for jobs table (allow all operations for authenticated users)
do $$
begin
    if not exists (
        select 1 from pg_policies 
        where schemaname = 'public' 
        and tablename = 'jobs' 
        and policyname = 'rls_auth_all_jobs'
    ) then
        create policy rls_auth_all_jobs on jobs 
        for all to authenticated 
        using (true) 
        with check (true);
    end if;
end $$;