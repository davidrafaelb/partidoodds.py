import math
import streamlit as st

# --------------------------
# Funciones Poisson
# --------------------------
def poisson_pmf(k, lam):
    return math.exp(-lam) * (lam**k) / math.factorial(k)

def decimales_to_probs(odds):
    inv = {k: 1.0/v for k,v in odds.items()}
    s = sum(inv.values())
    return {k: inv[k]/s for k in inv}

def match_probs_from_lambdas(lh, la, max_goals=10):
    p_home_win = p_draw = p_away_win = 0.0
    dist_h = [poisson_pmf(k, lh) for k in range(max_goals+1)]
    dist_a = [poisson_pmf(k, la) for k in range(max_goals+1)]
    for i in range(max_goals+1):
        for j in range(max_goals+1):
            p = dist_h[i]*dist_a[j]
            if i > j:
                p_home_win += p
            elif i == j:
                p_draw += p
            else:
                p_away_win += p
    return {
        'home_win': p_home_win,
        'draw': p_draw,
        'away_win': p_away_win,
        'dist_home': dist_h,
        'dist_away': dist_a
    }

def fit_lambdas_from_odds(odds, max_goals=10):
    market = decimales_to_probs(odds)
    target = (market['home'], market['draw'], market['away'])

    def loss(lh, la):
        m = match_probs_from_lambdas(lh, la, max_goals)
        return (m['home_win'] - target[0])**2 + (m['draw'] - target[1])**2 + (m['away_win'] - target[2])**2

    best = (1.5, 1.0)
    best_loss = float('inf')

    # búsqueda simple
    for lh in [i*0.1 for i in range(1, 81)]:   # 0.1 .. 8.0
        for la in [j*0.1 for j in range(1, 81)]:
            L = loss(lh, la)
            if L < best_loss:
                best_loss = L
                best = (lh, la)

    final = match_probs_from_lambdas(best[0], best[1], max_goals)
    return {
        'lambda_home': best[0],
        'lambda_away': best[1],
        'model_probs': (final['home_win'], final['draw'], final['away_win']),
        'dist_home': final['dist_home'],
        'dist_away': final['dist_away'],
        'market_probs': market
    }

# --------------------------
# Estimación de minutos de goles
# --------------------------
def expected_goal_minutes(lam, n_goals=3):
    """
    Estima los minutos esperados de los goles usando
    orden estadístico en proceso Poisson homogéneo.
    """
    if lam <= 0:
        return []
    minutes = [(k / (lam + 1)) * 90 for k in range(1, n_goals+1)]
    # solo goles dentro de los 90 min
    return [int(m) for m in minutes if m <= 90]

# --------------------------
# Streamlit UI
# --------------------------
st.title("⚽ Estimación de goles y minutos esperados según odds")

st.subheader("Ingresar odds (decimal)")
odd_home = st.number_input("Odd Local", value=2.20, format="%.2f")
odd_draw = st.number_input("Odd Empate", value=3.40, format="%.2f")
odd_away = st.number_input("Odd Visitante", value=3.20, format="%.2f")

odds = {'home': odd_home, 'draw': odd_draw, 'away': odd_away}

if st.button("Calcular"):
    res = fit_lambdas_from_odds(odds, max_goals=8)

    st.write("### λ (promedio de goles esperado)")
    st.write(f"Equipo local: **{res['lambda_home']:.2f}** goles")
    st.write(f"Equipo visitante: **{res['lambda_away']:.2f}** goles")

    # Distribución de goles esperados
    st.write("### Distribución de goles (probabilidades)")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Local:**")
        for k,p in enumerate(res['dist_home'][:6]):
            st.write(f"{k} goles: {p:.2%}")
    with col2:
        st.write("**Visitante:**")
        for k,p in enumerate(res['dist_away'][:6]):
            st.write(f"{k} goles: {p:.2%}")

    # Minutos esperados de goles
    st.write("### Minutos esperados de goles")
    mins_home = expected_goal_minutes(res['lambda_home'])
    mins_away = expected_goal_minutes(res['lambda_away'])
    st.write(f"Local (goles esperados en): {mins_home}")
    st.write(f"Visitante (goles esperados en): {mins_away}")

    # Probabilidades de mercado vs modelo
    st.write("### Comparación probabilidades 1X2")
    st.write("**Mercado (normalizado):**", res['market_probs'])
    st.write("**Modelo Poisson:**", {
        'home': res['model_probs'][0],
        'draw': res['model_probs'][1],
        'away': res['model_probs'][2]
    })
