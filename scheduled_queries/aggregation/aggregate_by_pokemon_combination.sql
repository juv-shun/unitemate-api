WITH t1 AS (
	SELECT namespace, match_id, pick_order, pokemon, result
	FROM "unitemate-api-prd"."processed-origin-prd"
    WHERE
        time between bin(@scheduled_runtime, 1d) - 1d AND bin(@scheduled_runtime, 1d)
        AND measure_name = 'user_result'
), base AS (
    SELECT DISTINCT t1.namespace, t1.pokemon, t2.pokemon AS pokemon2
    FROM t1
    CROSS JOIN t1 AS t2
    WHERE t1.pokemon != t2.pokemon
), allies AS (
	SELECT t1.namespace, t1.pokemon, t2.pokemon AS pokemon2, t1.match_id, t1.result
	FROM t1
	JOIN t1 AS t2 ON t1.namespace = t2.namespace AND t1.match_id = t2.match_id AND t1.pick_order = t2.pick_order
	WHERE t1.pokemon != t2.pokemon
), enemies AS (
	SELECT t1.namespace, t1.pokemon, t2.pokemon AS pokemon2, t1.match_id, t1.result
	FROM t1
	JOIN t1 AS t2 ON t1.namespace = t2.namespace AND t1.match_id = t2.match_id AND t1.pick_order != t2.pick_order
), ally_matches AS (
    SELECT namespace, pokemon, pokemon2, COUNT(DISTINCT match_id) AS ally_match_total
    FROM allies
    GROUP BY namespace, pokemon, pokemon2
), ally_win_matches AS (
    SELECT namespace, pokemon, pokemon2, COUNT(DISTINCT match_id) AS ally_win_total
    FROM allies
    WHERE result = 'win'
    GROUP BY namespace, pokemon, pokemon2
), enemy_matches AS (
    SELECT namespace, pokemon, pokemon2, COUNT(DISTINCT match_id) AS enemy_match_total
    FROM enemies
    GROUP BY namespace, pokemon, pokemon2
), enemy_win_matches AS (
    SELECT namespace, pokemon, pokemon2, COUNT(DISTINCT match_id) AS enemy_win_total
    FROM enemies
    WHERE result = 'win'
    GROUP BY namespace, pokemon, pokemon2
)

SELECT
    base.namespace,
    base.pokemon,
    base.pokemon2,
    bin(@scheduled_runtime, 1d) - 1d AS time,
    'aggregate_by_pokemon_combination' AS measure_name,
    COALESCE(ally_win_total, 0) AS ally_win_total,
    COALESCE(ally_match_total, 0) AS ally_match_total,
    COALESCE(enemy_win_total, 0) AS enemy_win_total,
    COALESCE(enemy_match_total, 0) AS enemy_match_total
FROM base
LEFT JOIN (
    SELECT namespace, pokemon, pokemon2, COUNT(DISTINCT match_id) AS ally_match_total
    FROM allies
    GROUP BY namespace, pokemon, pokemon2
) AS ally_matches
ON base.namespace = ally_matches.namespace
    AND base.pokemon = ally_matches.pokemon
    AND base.pokemon2 = ally_matches.pokemon2
LEFT JOIN (
    SELECT namespace, pokemon, pokemon2, COUNT(DISTINCT match_id) AS enemy_match_total
    FROM enemies
    GROUP BY namespace, pokemon, pokemon2
) AS enemy_matches
ON base.namespace = enemy_matches.namespace
    AND base.pokemon = enemy_matches.pokemon
    AND base.pokemon2 = enemy_matches.pokemon2
LEFT JOIN (
    SELECT namespace, pokemon, pokemon2, COUNT(DISTINCT match_id) AS ally_win_total
    FROM allies
    WHERE result = 'win'
    GROUP BY namespace, pokemon, pokemon2
) AS ally_win_matches
ON base.namespace = ally_win_matches.namespace
    AND base.pokemon = ally_win_matches.pokemon
    AND base.pokemon2 = ally_win_matches.pokemon2
LEFT JOIN (
    SELECT namespace, pokemon, pokemon2, COUNT(DISTINCT match_id) AS enemy_win_total
    FROM enemies
    WHERE result = 'win'
    GROUP BY namespace, pokemon, pokemon2
) AS enemy_win_matches
ON base.namespace = enemy_win_matches.namespace
    AND base.pokemon = enemy_win_matches.pokemon
    AND base.pokemon2 = enemy_win_matches.pokemon2
WHERE
    ally_match_total > 0 OR enemy_match_total > 0
ORDER BY namespace, pokemon, ally_match_total + enemy_match_total DESC
