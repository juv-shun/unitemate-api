WITH user_result AS (
    SELECT namespace, match_id, user_id, time, pick_order, result, pokemon, move1, move2
    FROM "unitemate-api-prd"."processed-origin-prd"
    WHERE time BETWEEN bin(@scheduled_runtime, 1d) - 1d AND bin(@scheduled_runtime, 1d)
        AND measure_name = 'user_result'
), match_result AS (
    SELECT namespace, match_id, time, winner
    FROM "unitemate-api-prd"."processed-origin-prd"
    WHERE time BETWEEN bin(@scheduled_runtime, 1d) - 1d AND bin(@scheduled_runtime, 1d)
        AND measure_name = 'match_result'
), ban_result AS (
    SELECT namespace, match_id, time, pick_order, banned_pokemon
    FROM "unitemate-api-prd"."processed-origin-prd"
    WHERE time BETWEEN bin(@scheduled_runtime, 1d) - 1d AND bin(@scheduled_runtime, 1d)
        AND measure_name = 'ban_result'
), match_ban AS (
    SELECT
        ban_result.namespace,
        ban_result.match_id,
        ban_result.time,
        ban_result.pick_order,
        CASE
            WHEN ban_result.pick_order = match_result.winner
            THEN 'win' ELSE 'lose'
        END AS result,
        banned_pokemon
    FROM ban_result
    JOIN match_result ON
        ban_result.namespace = match_result.namespace
        AND ban_result.match_id = match_result.match_id
        AND ban_result.time = match_result.time
)

SELECT
    base.namespace,
    base.pokemon,
    bin(@scheduled_runtime, 1d) - 1d AS time,
    'aggregate_by_pokemon' AS measure_name,
    COALESCE(first_picked, 0) AS first_picked,
    COALESCE(first_picked_win, 0) AS first_picked_win,
    COALESCE(second_picked, 0) AS second_picked,
    COALESCE(second_picked_win, 0) AS second_picked_win,
    COALESCE(first_banned, 0) AS first_banned,
    COALESCE(first_banned_win, 0) AS first_banned_win,
    COALESCE(second_banned, 0) AS second_banned,
    COALESCE(second_banned_win, 0) AS second_banned_win,
    COALESCE(banned, 0) AS banned,
    COALESCE(match_total, 0) AS match_total
FROM (
    SELECT DISTINCT namespace, pokemon
    FROM user_result
) AS base
LEFT JOIN (
    SELECT namespace, pokemon, COUNT(DISTINCT match_id) AS first_picked
    FROM user_result
    WHERE pick_order = 'first'
    GROUP BY namespace, pokemon
) AS first_picked_table
ON base.namespace = first_picked_table.namespace AND base.pokemon = first_picked_table.pokemon
LEFT JOIN (
    SELECT namespace, pokemon, COUNT(DISTINCT match_id) AS second_picked
    FROM user_result
    WHERE pick_order = 'second'
    GROUP BY namespace, pokemon
) AS second_picked_table
ON base.namespace = second_picked_table.namespace AND base.pokemon = second_picked_table.pokemon
LEFT JOIN (
    SELECT namespace, pokemon, COUNT(DISTINCT match_id) AS first_picked_win
    FROM user_result
    WHERE pick_order = 'first' AND result = 'win'
    GROUP BY namespace, pokemon
) AS first_picked_win_table
ON base.namespace = first_picked_win_table.namespace AND base.pokemon = first_picked_win_table.pokemon
LEFT JOIN (
    SELECT namespace, pokemon, COUNT(DISTINCT match_id) AS second_picked_win
    FROM user_result
    WHERE pick_order = 'second' AND result = 'win'
    GROUP BY namespace, pokemon
) AS second_picked_win_table
ON base.namespace = second_picked_win_table.namespace AND base.pokemon = second_picked_win_table.pokemon
LEFT JOIN (
    SELECT namespace, banned_pokemon AS pokemon, COUNT(DISTINCT match_id) AS first_banned
    FROM match_ban
    WHERE pick_order = 'first'
    GROUP BY namespace, banned_pokemon
) AS first_banned_table
ON base.namespace = first_banned_table.namespace AND base.pokemon = first_banned_table.pokemon
LEFT JOIN (
    SELECT namespace, banned_pokemon AS pokemon, COUNT(DISTINCT match_id) AS second_banned
    FROM match_ban
    WHERE pick_order = 'second'
    GROUP BY namespace, banned_pokemon
) AS second_banned_table
ON base.namespace = second_banned_table.namespace AND base.pokemon = second_banned_table.pokemon
LEFT JOIN (
    SELECT namespace, banned_pokemon AS pokemon, COUNT(DISTINCT match_id) AS first_banned_win
    FROM match_ban
    WHERE pick_order = 'first' AND result = 'win'
    GROUP BY namespace, banned_pokemon
) AS first_banned_win_table
ON base.namespace = first_banned_win_table.namespace AND base.pokemon = first_banned_win_table.pokemon
LEFT JOIN (
    SELECT namespace, banned_pokemon AS pokemon, COUNT(DISTINCT match_id) AS second_banned_win
    FROM match_ban
    WHERE pick_order = 'second' AND result = 'win'
    GROUP BY namespace, banned_pokemon
) AS second_banned_win_table
ON base.namespace = second_banned_win_table.namespace AND base.pokemon = second_banned_win_table.pokemon
LEFT JOIN (
    SELECT namespace, banned_pokemon AS pokemon, COUNT(DISTINCT match_id) AS banned
    FROM match_ban
    GROUP BY namespace, banned_pokemon
) AS banned_table
ON base.namespace = banned_table.namespace AND base.pokemon = banned_table.pokemon
LEFT JOIN (
    SELECT namespace, COUNT(DISTINCT match_id) as match_total
    FROM match_result
    GROUP BY namespace
) AS total
ON base.namespace = total.namespace
