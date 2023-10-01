SELECT
    pokemon,
    date(time) AS date,
    first_picked,
    first_picked_win,
    second_picked,
    second_picked_win,
    first_banned,
    first_banned_win,
    second_banned,
    second_banned_win,
    banned,
    match_total
FROM "{db}"."{table}"
WHERE
    time = bin(now(), 1d) - 1d
    AND namespace = 'default'
    AND measure_name = 'aggregate_by_pokemon'
ORDER BY first_picked + second_picked + banned DESC
