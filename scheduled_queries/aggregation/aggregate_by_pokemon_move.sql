WITH user_result AS (
    SELECT namespace, match_id, user_id, time, pick_order, result, pokemon, move1, move2, rate
    FROM "unitemate-api-prd"."processed-origin-prd"
    WHERE time BETWEEN bin(@scheduled_runtime, 1d) - 1d AND bin(@scheduled_runtime, 1d)
        AND measure_name = 'user_result'
), match_result AS (
    SELECT namespace, match_id, time, winner
    FROM "unitemate-api-prd"."processed-origin-prd"
    WHERE time BETWEEN bin(@scheduled_runtime, 1d) - 1d AND bin(@scheduled_runtime, 1d)
        AND measure_name = 'match_result'
)

SELECT
    base.namespace,
    base.pokemon,
    base.move1,
    base.move2,
    bin(@scheduled_runtime, 1d) - 1d AS time,
    'aggregate_by_pokemon_move' AS measure_name,
    COALESCE(first_picked, 0) AS first_picked,
    COALESCE(second_picked, 0) AS second_picked,
    COALESCE(first_picked_win, 0) AS first_picked_win,
    COALESCE(second_picked_win, 0) AS second_picked_win,
    COALESCE(match_total, 0) AS match_total
FROM (
    SELECT DISTINCT namespace, pokemon, move1, move2
    FROM user_result
) AS base
LEFT JOIN (
    SELECT namespace, pokemon, move1, move2, COUNT(DISTINCT match_id) AS first_picked
    FROM user_result
    WHERE pick_order = 'first'
    GROUP BY namespace, pokemon, move1, move2
) AS first_picked_table
ON base.namespace = first_picked_table.namespace AND base.pokemon = first_picked_table.pokemon
    AND base.move1 = first_picked_table.move1 AND base.move2 = first_picked_table.move2
LEFT JOIN (
    SELECT namespace, pokemon, move1, move2, COUNT(DISTINCT match_id) AS second_picked
    FROM user_result
    WHERE pick_order = 'second'
    GROUP BY namespace, pokemon, move1, move2
) AS second_picked_table
ON base.namespace = second_picked_table.namespace AND base.pokemon = second_picked_table.pokemon
    AND base.move1 = second_picked_table.move1 AND base.move2 = second_picked_table.move2
LEFT JOIN (
    SELECT namespace, pokemon, move1, move2, COUNT(DISTINCT match_id) AS first_picked_win
    FROM user_result
    WHERE pick_order = 'first' AND result = 'win'
    GROUP BY namespace, pokemon, move1, move2
) AS first_picked_win_table
ON base.namespace = first_picked_win_table.namespace AND base.pokemon = first_picked_win_table.pokemon
    AND base.move1 = first_picked_win_table.move1 AND base.move2 = first_picked_win_table.move2
LEFT JOIN (
    SELECT namespace, pokemon, move1, move2, COUNT(DISTINCT match_id) AS second_picked_win
    FROM user_result
    WHERE pick_order = 'second' AND result = 'win'
    GROUP BY namespace, pokemon, move1, move2
) AS second_picked_win_table
ON base.namespace = second_picked_win_table.namespace AND base.pokemon = second_picked_win_table.pokemon
    AND base.move1 = second_picked_win_table.move1 AND base.move2 = second_picked_win_table.move2
LEFT JOIN (
    SELECT namespace, COUNT(DISTINCT match_id) as match_total
    FROM match_result
    GROUP BY namespace
) AS total
ON base.namespace = total.namespace
