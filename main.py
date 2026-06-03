import matplotlib
matplotlib.use('MacOSX')
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import numpy as np

# ── Palette (matches CATCHY style) ───────────────────────────────────────────
BG    = '#0a0f1e'
PANEL = '#1a1f2e'
C_E   = '#4fc3f7'   # electric  — cyan
C_F   = '#ef5350'   # fuel      — red
C_H   = '#ce93d8'   # hybrid    — purple
C_LD  = '#aed581'   # L/D       — green
C_PWR = '#ffcc02'   # power     — yellow
WHITE = 'white'

# ── Physics ───────────────────────────────────────────────────────────────────
G          = 9.81
STORE_ELEC = 0.80   # fraction of prop budget that is battery
STORE_FUEL = 0.85   # fraction of prop budget that is fuel
HYB_BFRAC  = 0.40   # battery fraction inside hybrid budget

def isa_rho(h):
    T = 288.15 - 0.0065 * h
    return 101325.0 * (T / 288.15) ** 5.2561 / (287.05 * T)

def compute(mtow, S, AR, CD0, e, CLmax, alt, fprop, batt_whkg, eta_e, fhv_whkg, eta_f):
    rho = isa_rho(alt)
    W   = mtow * G
    mp  = mtow * fprop

    Vs = np.sqrt(2 * W / (rho * S * CLmax))
    V  = np.linspace(max(Vs * 1.05, 5.0), 90.0, 600)   # m/s up to 324 km/h

    CL = 2 * W / (rho * V**2 * S)
    CD = CD0 + CL**2 / (np.pi * AR * e)
    D  = 0.5 * rho * V**2 * S * CD
    LD = CL / CD
    Pk = D * V / 1000   # kW

    Ee = mp * STORE_ELEC * batt_whkg * 3600 * eta_e
    Ef = mp * STORE_FUEL * fhv_whkg  * 3600 * eta_f
    Eh = (mp * HYB_BFRAC       * STORE_ELEC * batt_whkg * 3600 * eta_e +
          mp * (1 - HYB_BFRAC) * STORE_FUEL * fhv_whkg  * 3600 * eta_f)

    return dict(
        V=V * 3.6, Vs=Vs * 3.6,
        Re=Ee / D / 1000,
        Rf=Ef / D / 1000,
        Rh=Eh / D / 1000,
        LD=LD, Pk=Pk,
    )

# ── Default values ────────────────────────────────────────────────────────────
D0 = dict(
    mtow=22.0, S=1.0, AR=14.0, CD0=0.025,
    e=0.85, CLmax=1.30, alt=2000,
    fprop=0.38, batt=250, eta_e=0.85,
    fhv=11800, eta_f=0.27,
)

# ── Figure layout ─────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(13, 10))
fig.patch.set_facecolor(BG)

ax_r  = fig.add_axes([0.07, 0.40, 0.88, 0.54])   # range vs speed  (main)
ax_ld = fig.add_axes([0.07, 0.27, 0.40, 0.11])   # L/D
ax_pw = fig.add_axes([0.53, 0.27, 0.40, 0.11])   # power required

for ax in (ax_r, ax_ld, ax_pw):
    ax.set_facecolor(BG)
    ax.tick_params(colors=WHITE, labelsize=8)
    ax.grid(True, alpha=0.12, color=WHITE)
    for sp in ax.spines.values():
        sp.set_edgecolor('#333355')

# ── Initial curves ────────────────────────────────────────────────────────────
c = compute(**D0)
V = c['V']

# Range
le, = ax_r.plot(V, c['Re'], color=C_E, lw=2.5, label='Electric')
lf, = ax_r.plot(V, c['Rf'], color=C_F, lw=2.5, label='Fuel (ICE)')
lh, = ax_r.plot(V, c['Rh'], color=C_H, lw=2.5, label=f'Hybrid ({int(HYB_BFRAC*100)}% battery)')

de, = ax_r.plot([], [], 'o', color=C_E, ms=10, zorder=5)
df, = ax_r.plot([], [], 'o', color=C_F, ms=10, zorder=5)
dh, = ax_r.plot([], [], 'o', color=C_H, ms=10, zorder=5)

hl_tgt = ax_r.axhline(1000, color='goldenrod', ls='--', lw=1.5, alpha=0.75, label='1 000 km target')
vl_vmax = ax_r.axvline(300, color=C_F, ls=':', lw=1.5, alpha=0.55, label='V_max 300 km/h')
vl_st_r = ax_r.axvline(c['Vs'], color='grey', ls=':', lw=1.0, alpha=0.5)

ax_r.set_title('Long-Range Drone — Range vs. Cruise Speed Trade Study',
               color=WHITE, fontsize=12, pad=8)
ax_r.set_ylabel('Range  (km)', color=WHITE, fontsize=9)
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

# ── Column headers ────────────────────────────────────────────────────────────
fig.text(0.27, 0.235, 'AIRFRAME',   color=C_E,  fontsize=9, ha='center', fontweight='bold')
fig.text(0.73, 0.235, 'PROPULSION', color=C_F,  fontsize=9, ha='center', fontweight='bold')

# ── Sliders ───────────────────────────────────────────────────────────────────
SY  = [0.205, 0.160, 0.115, 0.070]   # four rows
SH  = 0.016

ax_sl = [fig.add_axes([0.07, y, 0.36, SH]) for y in SY]
ax_sr = [fig.add_axes([0.57, y, 0.36, SH]) for y in SY]
for ax in ax_sl + ax_sr:
    ax.set_facecolor(PANEL)

sl_mtow = Slider(ax_sl[0], 'MTOW  (kg)',       5,   60,  valinit=D0['mtow'],  color=C_E)
sl_S    = Slider(ax_sl[1], 'Wing area  (m²)', 0.2,  4.0, valinit=D0['S'],     color='#81d4fa')
sl_AR   = Slider(ax_sl[2], 'Aspect ratio',    5,   25,   valinit=D0['AR'],    color='#81d4fa')
sl_CD0  = Slider(ax_sl[3], 'CD₀',            0.01, 0.06, valinit=D0['CD0'],   color='#b3e5fc',
                 valfmt='%.3f')

sl_fp   = Slider(ax_sr[0], 'Prop mass frac.', 0.10, 0.65, valinit=D0['fprop'], color=C_F)
sl_bt   = Slider(ax_sr[1], 'Battery  (Wh/kg)', 100, 500,  valinit=D0['batt'],  color=C_H)
sl_eta  = Slider(ax_sr[2], 'ICE efficiency',  0.18, 0.40, valinit=D0['eta_f'], color='#f48fb1')
sl_alt  = Slider(ax_sr[3], 'Altitude  (m)',      0, 5000, valinit=D0['alt'],   color=C_LD)

all_sliders = [sl_mtow, sl_S, sl_AR, sl_CD0, sl_fp, sl_bt, sl_eta, sl_alt]
for sl in all_sliders:
    sl.label.set_color(WHITE)
    sl.valtext.set_color(WHITE)

# Reset button
ax_btn = fig.add_axes([0.43, 0.015, 0.14, 0.032])
ax_btn.set_facecolor(PANEL)
btn = Button(ax_btn, 'Reset', color=PANEL, hovercolor='#2a3f5e')
btn.label.set_color(WHITE)

# ── Redraw callback ───────────────────────────────────────────────────────────
def redraw(_=None):
    c = compute(
        mtow=sl_mtow.val, S=sl_S.val, AR=sl_AR.val,
        CD0=sl_CD0.val,   e=D0['e'],  CLmax=D0['CLmax'],
        alt=sl_alt.val,   fprop=sl_fp.val,
        batt_whkg=sl_bt.val, eta_e=D0['eta_e'],
        fhv_whkg=D0['fhv'],  eta_f=sl_eta.val,
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

    # Rescale each axis
    for ax, ys in ((ax_r,  [c['Re'], c['Rf'], c['Rh']]),
                   (ax_ld, [c['LD']]),
                   (ax_pw, [c['Pk']])):
        all_y = np.concatenate(ys)
        mn, mx = np.nanmin(all_y), np.nanmax(all_y)
        pad = max((mx - mn) * 0.1, 1.0)
        ax.set_ylim(max(0, mn - pad), mx + pad)
        ax.set_xlim(V[0], V[-1])

    # Status line
    ie = int(np.argmax(c['Re']))
    if_ = int(np.argmax(c['Rf']))
    ih = int(np.argmax(c['Rh']))
    Re, Rf, Rh = c['Re'][ie], c['Rf'][if_], c['Rh'][ih]
    tgt = '✓' if max(Re, Rf, Rh) >= 1000 else '✗'
    status.set_text(
        f"Electric: {Re:.0f} km @ {V[ie]:.0f} km/h    "
        f"Fuel: {Rf:.0f} km @ {V[if_]:.0f} km/h    "
        f"Hybrid: {Rh:.0f} km @ {V[ih]:.0f} km/h    "
        f"1000 km target: {tgt}"
    )
    fig.canvas.draw_idle()

def reset(_):
    keys = ['mtow', 'S', 'AR', 'CD0', 'fprop', 'batt', 'eta_f', 'alt']
    for sl, k in zip(all_sliders, keys):
        sl.set_val(D0[k])

for sl in all_sliders:
    sl.on_changed(redraw)
btn.on_clicked(reset)

redraw()
plt.show()
