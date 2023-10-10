SELECT
    pokemon,
    pokemon2,
    CASE
        WHEN measure_name = 'aggregate_ally_pokemon'
        THEN 'ally' ELSE 'enemy'
    END AS team,
    result,
    date(time) AS date,
    match_total
FROM "{db}"."{table}"
WHERE
    time = bin(now(), 1d) - 1d
    AND namespace = '{namespace}'
    AND measure_name IN ('aggregate_ally_pokemon', 'aggregate_enemy_pokemon')
ORDER BY pokemon, pokemon2
