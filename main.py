import matplotlib
matplotlib.use('MacOSX')
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import numpy as np

# ── Palette (matches CATCHY style) ───────────────────────────────────────────
BG    = '#0a0f1e'
PANEL = '#1a1f2e'
C_E   = '#4fc3f7'
C_F   = '#ef5350'
C_H   = '#ce93d8'
C_LD  = '#aed581'
C_PWR = '#ffcc02'
WHITE = 'white'

# ── Physics ───────────────────────────────────────────────────────────────────
G          = 9.81
STORE_ELEC = 0.80   # fraction of electric prop budget that is battery
STORE_FUEL = 0.85   # fraction of ICE prop budget that is fuel
HYB_BFRAC  = 0.40   # battery share of hybrid prop budget
ETA_PROP   = 0.85   # propeller efficiency (shaft → thrust)

def isa_rho(h):
    T = 288.15 - 0.0065 * h
    return 101325.0 * (T / 288.15) ** 5.2561 / (287.05 * T)

def compute(mtow, S, AR, CD0, e, CLmax, alt, m_prop, batt_whkg, eta_e, fhv_whkg, eta_f):
    rho = isa_rho(alt)
    W   = mtow * G
    mp  = min(m_prop, max(mtow - 2.0, 0.0))   # can't exceed airframe budget

    Vs = np.sqrt(2 * W / (rho * S * CLmax))
    V  = np.linspace(max(Vs * 1.05, 5.0), 90.0, 600)

    # ── Aerodynamics at initial (full) weight ─────────────────────────────────
    CL = 2 * W / (rho * V**2 * S)
    CD = CD0 + CL**2 / (np.pi * AR * e)
    D  = 0.5 * rho * V**2 * S * CD
    LD = CL / CD

    # Shaft power = aerodynamic power / propeller efficiency
    Pk = D * V / ETA_PROP / 1000   # kW

    # ── Electric range ────────────────────────────────────────────────────────
    # Batteries don't lose mass → weight stays constant → R = E_useful / D
    m_batt  = mp * STORE_ELEC
    E_elec  = m_batt * batt_whkg * 3600 * eta_e * ETA_PROP   # J (motor → shaft → thrust)
    Re      = E_elec / D / 1000                               # km

    # ── Fuel (ICE) range — Breguet with average L/D ──────────────────────────
    # At fixed altitude + speed, L/D drifts as fuel burns and weight drops.
    # Averaging start and end L/D is the standard preliminary-design
    # approximation for constant-altitude, constant-speed cruise.
    m_fuel  = mp * STORE_FUEL
    m_end_f = mtow - m_fuel
    if m_end_f > 0.5 and m_fuel > 0:
        CL_end_f = 2 * (m_end_f * G) / (rho * V**2 * S)
        CD_end_f = CD0 + CL_end_f**2 / (np.pi * AR * e)
        LD_avg_f = 0.5 * (LD + CL_end_f / CD_end_f)
        Rf = (eta_f * fhv_whkg * 3600 / G) * LD_avg_f * np.log(mtow / m_end_f) / 1000
    else:
        Rf = np.zeros_like(V)

    # ── Hybrid range — fuel first (avg L/D Breguet), then electric ───────────
    m_fuel_h = mp * (1 - HYB_BFRAC) * STORE_FUEL
    m_batt_h = mp * HYB_BFRAC * STORE_ELEC
    m_end_h  = mtow - m_fuel_h

    if m_end_h > 0.5 and m_fuel_h > 0:
        # Phase 1: fuel burn with average L/D
        CL_end_h = 2 * (m_end_h * G) / (rho * V**2 * S)
        CD_end_h = CD0 + CL_end_h**2 / (np.pi * AR * e)
        LD_avg_h = 0.5 * (LD + CL_end_h / CD_end_h)
        R_fuel_h = (eta_f * fhv_whkg * 3600 / G) * LD_avg_h * np.log(mtow / m_end_h) / 1000

        # Phase 2: electric on the now-lighter drone
        W_post   = m_end_h * G
        CL_post  = 2 * W_post / (rho * V**2 * S)
        CD_post  = CD0 + CL_post**2 / (np.pi * AR * e)
        D_post   = 0.5 * rho * V**2 * S * CD_post
        E_batt_h = m_batt_h * batt_whkg * 3600 * eta_e * ETA_PROP
        R_batt_h = E_batt_h / D_post / 1000

        Rh = R_fuel_h + R_batt_h
    else:
        Rh = Re

    return dict(
        V=V * 3.6, Vs=Vs * 3.6,
        Re=Re, Rf=Rf, Rh=Rh,
        LD=LD, Pk=Pk,
    )

# ── Defaults ──────────────────────────────────────────────────────────────────
D0 = dict(
    mtow=22.0, S=1.0, AR=14.0, CD0=0.025,
    e=0.85, CLmax=1.30, alt=2000,
    m_prop=8.4, batt_whkg=250, eta_e=0.85,   # m_prop = 38% of 22 kg default
    fhv_whkg=11800, eta_f=0.27,
)

# ── Figure ────────────────────────────────────────────────────────────────────
# Layout (all in figure-fraction coordinates, figure is 14 × 12 inches):
#   Main range plot  : y = 0.54 → 0.97
#   L/D + Power plots: y = 0.37 → 0.50  (gap of 0.04 below main plot)
#   Column headers   : y = 0.33
#   Slider rows      : y = 0.28, 0.22, 0.16, 0.10
#   Reset button     : y = 0.03
fig = plt.figure(figsize=(14, 12))
fig.patch.set_facecolor(BG)

ax_r  = fig.add_axes([0.07, 0.60, 0.88, 0.37])   # main:        60% → 97%
ax_ld = fig.add_axes([0.07, 0.37, 0.40, 0.14])   # L/D:         37% → 51%  gap = 9%
ax_pw = fig.add_axes([0.53, 0.37, 0.40, 0.14])   # Power req.:  37% → 51%

for ax in (ax_r, ax_ld, ax_pw):
    ax.set_facecolor(BG)
    ax.tick_params(colors=WHITE, labelsize=8)
    ax.grid(True, alpha=0.12, color=WHITE)
    for sp in ax.spines.values():
        sp.set_edgecolor('#333355')

# ── Initial curves ────────────────────────────────────────────────────────────
c = compute(**D0)
V = c['V']

le, = ax_r.plot(V, c['Re'], color=C_E, lw=2.5, label='Electric')
lf, = ax_r.plot(V, c['Rf'], color=C_F, lw=2.5, label='Fuel (ICE)')
lh, = ax_r.plot(V, c['Rh'], color=C_H, lw=2.5, label=f'Hybrid ({int(HYB_BFRAC*100)}% battery)')

de, = ax_r.plot([], [], 'o', color=C_E, ms=10, zorder=5)
df, = ax_r.plot([], [], 'o', color=C_F, ms=10, zorder=5)
dh, = ax_r.plot([], [], 'o', color=C_H, ms=10, zorder=5)

ax_r.axhline(1000, color='goldenrod', ls='--', lw=1.5, alpha=0.75, label='1 000 km target')
ax_r.axvline(300,  color=C_F,         ls=':',  lw=1.5, alpha=0.55, label='V_max 300 km/h')
vl_st_r = ax_r.axvline(c['Vs'], color='grey', ls=':', lw=1.0, alpha=0.5)

ax_r.set_title('Long-Range Drone — Range vs. Cruise Speed Trade Study',
               color=WHITE, fontsize=12, pad=8)
ax_r.set_ylabel('Range  (km)',          color=WHITE, fontsize=9)
ax_r.set_xlabel('Cruise Speed  (km/h)', color=WHITE, fontsize=9)
ax_r.legend(loc='upper right', facecolor=PANEL, labelcolor=WHITE,
            edgecolor='#333355', fontsize=8)

status = ax_r.text(0.01, 0.97, '', transform=ax_r.transAxes,
                   color=WHITE, fontsize=9, va='top', family='monospace')

# L/D
ll, = ax_ld.plot(V, c['LD'], color=C_LD, lw=2)
dl, = ax_ld.plot([], [], 'o', color=C_LD, ms=7)
vl_st_l = ax_ld.axvline(c['Vs'], color='grey', ls=':', lw=1, alpha=0.5)
ax_ld.set_title('Lift-to-Drag Ratio', color=WHITE, fontsize=9)
ax_ld.set_ylabel('L/D',           color=WHITE, fontsize=8)
ax_ld.set_xlabel('Speed  (km/h)', color=WHITE, fontsize=8)

# Power
lp, = ax_pw.plot(V, c['Pk'], color=C_PWR, lw=2)
dp, = ax_pw.plot([], [], 'o', color=C_PWR, ms=7)
vl_st_p = ax_pw.axvline(c['Vs'], color='grey', ls=':', lw=1, alpha=0.5)
ax_pw.set_title('Power Required',  color=WHITE, fontsize=9)
ax_pw.set_ylabel('Power  (kW)',   color=WHITE, fontsize=8)
ax_pw.set_xlabel('Speed  (km/h)', color=WHITE, fontsize=8)

# ── Slider layout — 6 sliders in a single centred column ─────────────────────
SX, SW = 0.20, 0.60
SH = 0.022
SY = [0.225, 0.178, 0.131, 0.084, 0.037, -0.010]

ax_s = [fig.add_axes([SX, y, SW, SH]) for y in SY]
for ax in ax_s:
    ax.set_facecolor(PANEL)

sl_mtow = Slider(ax_s[0], 'MTOW (kg)',        5,   60,  valinit=D0['mtow'],     color=C_E)
sl_prop = Slider(ax_s[1], 'Prop mass (kg)',   1,   30,  valinit=D0['m_prop'],   color=C_F)
sl_S    = Slider(ax_s[2], 'Wing area (m²)',  0.2,  4.0, valinit=D0['S'],        color='#81d4fa')
sl_AR   = Slider(ax_s[3], 'Aspect ratio',    5,    25,  valinit=D0['AR'],       color='#81d4fa')
sl_alt  = Slider(ax_s[4], 'Altitude (m)',    0,  5000,  valinit=D0['alt'],      color=C_LD)
sl_bt   = Slider(ax_s[5], 'Battery (Wh/kg)', 100, 500,  valinit=D0['batt_whkg'], color=C_H)

all_sliders = [sl_mtow, sl_prop, sl_S, sl_AR, sl_alt, sl_bt]
for sl in all_sliders:
    sl.label.set_color(WHITE)
    sl.valtext.set_color(WHITE)

ax_btn = fig.add_axes([0.43, -0.042, 0.14, 0.028])
ax_btn.set_facecolor(PANEL)
btn = Button(ax_btn, 'Reset', color=PANEL, hovercolor='#2a3f5e')
btn.label.set_color(WHITE)

# ── Callbacks ─────────────────────────────────────────────────────────────────
def redraw(_=None):
    c = compute(
        mtow=sl_mtow.val, S=sl_S.val,    AR=sl_AR.val,
        CD0=D0['CD0'],    e=D0['e'],     CLmax=D0['CLmax'],
        alt=sl_alt.val,   m_prop=sl_prop.val,
        batt_whkg=sl_bt.val,             eta_e=D0['eta_e'],
        fhv_whkg=D0['fhv_whkg'],         eta_f=D0['eta_f'],
    )
    V = c['V']

    le.set_data(V, c['Re']); lf.set_data(V, c['Rf']); lh.set_data(V, c['Rh'])
    ll.set_data(V, c['LD']); lp.set_data(V, c['Pk'])

    for line, R, dot in ((le, c['Re'], de), (lf, c['Rf'], df), (lh, c['Rh'], dh)):
        i = int(np.argmax(R))
        dot.set_data([V[i]], [R[i]])

    iLD = int(np.argmax(c['LD'])); dl.set_data([V[iLD]], [c['LD'][iLD]])
    iP  = int(np.argmin(c['Pk'])); dp.set_data([V[iP]],  [c['Pk'][iP]])

    vs = c['Vs']
    for vl in (vl_st_r, vl_st_l, vl_st_p):
        vl.set_xdata([vs, vs])

    for ax, ys in ((ax_r,  [c['Re'], c['Rf'], c['Rh']]),
                   (ax_ld, [c['LD']]),
                   (ax_pw, [c['Pk']])):
        all_y = np.concatenate(ys)
        mn, mx = np.nanmin(all_y), np.nanmax(all_y)
        pad = max((mx - mn) * 0.1, 1.0)
        ax.set_ylim(max(0, mn - pad), mx + pad)
        ax.set_xlim(V[0], V[-1])

    ie, if_, ih = int(np.argmax(c['Re'])), int(np.argmax(c['Rf'])), int(np.argmax(c['Rh']))
    Re, Rf, Rh  = c['Re'][ie], c['Rf'][if_], c['Rh'][ih]
    tgt = '✓' if max(Re, Rf, Rh) >= 1000 else '✗'
    status.set_text(
        f"Electric: {Re:.0f} km @ {V[ie]:.0f} km/h    "
        f"Fuel: {Rf:.0f} km @ {V[if_]:.0f} km/h    "
        f"Hybrid: {Rh:.0f} km @ {V[ih]:.0f} km/h    "
        f"1000 km target: {tgt}"
    )
    fig.canvas.draw_idle()

def reset(_):
    sl_mtow.set_val(D0['mtow']); sl_prop.set_val(D0['m_prop'])
    sl_S.set_val(D0['S']);       sl_AR.set_val(D0['AR'])
    sl_alt.set_val(D0['alt']);   sl_bt.set_val(D0['batt_whkg'])

for sl in all_sliders:
    sl.on_changed(redraw)
btn.on_clicked(reset)

redraw()
plt.show()
