WITH user_result AS (
    SELECT namespace, match_id, user_id, time, pick_order, result, pokemon, move1, move2, rate
    FROM "unitemate-api-prd"."processed-origin-prd"
    WHERE time BETWEEN bin(@scheduled_runtime, 1d) - 1d AND bin(@scheduled_runtime, 1d)
        AND measure_name = 'user_result'
), match_result AS (
    SELECT namespace, match_id, time, winner, first_banned_pokemon0, second_banned_pokemon0
    FROM "unitemate-api-prd"."processed-origin-prd"
    WHERE time BETWEEN bin(@scheduled_runtime, 1d) - 1d AND bin(@scheduled_runtime, 1d)
        AND measure_name = 'match_result'
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
    (
        SELECT COUNT(DISTINCT match_id)
        FROM match_result
    ) AS match_total
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
    SELECT namespace, first_banned_pokemon0 AS pokemon, COUNT(DISTINCT match_id) AS first_banned
    FROM match_result
    GROUP BY namespace, first_banned_pokemon0
) AS first_banned_table
ON base.namespace = first_banned_table.namespace AND base.pokemon = first_banned_table.pokemon
LEFT JOIN (
    SELECT namespace, second_banned_pokemon0 AS pokemon, COUNT(DISTINCT match_id) AS second_banned
    FROM match_result
    GROUP BY namespace, second_banned_pokemon0
) AS second_banned_table
ON base.namespace = second_banned_table.namespace AND base.pokemon = second_banned_table.pokemon
LEFT JOIN (
    SELECT namespace, first_banned_pokemon0 AS pokemon, COUNT(DISTINCT match_id) AS first_banned_win
    FROM match_result
    WHERE winner = 'first'
    GROUP BY namespace, first_banned_pokemon0
) AS first_banned_win_table
ON base.namespace = first_banned_win_table.namespace AND base.pokemon = first_banned_win_table.pokemon
LEFT JOIN (
    SELECT namespace, second_banned_pokemon0 AS pokemon, COUNT(DISTINCT match_id) AS second_banned_win
    FROM match_result
    WHERE winner = 'second'
    GROUP BY namespace, second_banned_pokemon0
) AS second_banned_win_table
ON base.namespace = second_banned_win_table.namespace AND base.pokemon = second_banned_win_table.pokemon
LEFT JOIN (
    SELECT namespace, banned_pokemon AS pokemon, COUNT(DISTINCT match_id) AS banned
    FROM (
        SELECT namespace, match_id, first_banned_pokemon0 AS banned_pokemon
        FROM match_result
        UNION ALL
        SELECT namespace, match_id, second_banned_pokemon0 AS banned_pokemon
        FROM match_result
    )
    GROUP BY namespace, banned_pokemon
) AS banned_table
ON base.namespace = banned_table.namespace AND base.pokemon = banned_table.pokemon
