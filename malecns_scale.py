from fractions import Fraction as F

# ---- official measurements (as given in fragment) ----
N        = 166_700          # neurons, MaleCNS v1.0
E        = 25_582_938       # deduplicated directed neuron-pair edges
S        = 124_177_617      # synaptic contact points (boutons / T-bars)
N_fw     = 139_255          # FlyWire FAFB proofread neurons
S_fw     = 54_500_000       # FlyWire FAFB contacts (approx, 54.5e6)

def show(name, val, fmt="{:.12g}"):
    print(f"{name:44s} = {fmt.format(val)}")
    return val

print("=" * 74)
print("2. DENSITY / FILL FRACTION")
print("=" * 74)
pairs = N * (N - 1)
show("N*(N-1)  ordered pairs", pairs, "{:,}")
rho = F(E, pairs)
show("rho = E/(N(N-1))", float(rho), "{:.6e}")
show("rho [%]", float(rho) * 100, "{:.10f}")
K = 1 / float(rho)
show("K = 1/rho  (1 in K)", K, "{:.4f}")
print(f"  -> 1 connection per ~{round(K):,} ordered pairs")
show("density of G(N,0.5) random digraph", 0.5, "{:.1f}")
show("ratio rho / 0.5", float(rho) / 0.5, "{:.4e}")
show("percent of pairs that are EMPTY", (1 - float(rho)) * 100, "{:.10f}")
show("E if complete digraph (N(N-1))", pairs, "{:,}")
show("E present / E complete", E / pairs, "{:.6e}")

print()
print("=" * 74)
print("3. MEAN CONTACTS PER CONNECTION")
print("=" * 74)
sbar = F(S, E)
show("sbar = S/E", float(sbar), "{:.8f}")
print(f"  -> each surviving edge carries on average {float(sbar):.6f} contact points")
print(f"  -> contacts per edge is an integer >= 1, so sbar >= 1: {float(sbar) >= 1}")
print("""
Symbolic threshold model
    p_k  = fraction of the E edges having exactly k contacts,  sum_k p_k = 1
    E_{>=5} = E * sum_{k>=5} p_k                (surviving EDGE count)
    S_surv  = E * sum_{k>=5} k p_k              (contacts kept)
    S_all   = E * sum_{k>=1} k p_k = E * sbar = S
Removing 1..4-contact edges changes the EDGE count a lot but contacts only slightly,
because sum_{k>=5} k p_k is close to sum_{k>=1} k p_k when the tail carries few contacts.
""")
# illustrative heavy tail -- NOT MaleCNS data
pk = {k: (k ** -2.2) for k in range(1, 60)}
Z = sum(pk.values())
pk = {k: v / Z for k, v in pk.items()}
keep = sum(pk[k] for k in pk if k >= 5)
w_keep = sum(k * pk[k] for k in pk if k >= 5)
w_all = sum(k * pk[k] for k in pk)
print("  ILLUSTRATIVE heavy tail p_k ~ k^-2.2 (NOT MaleCNS data):")
print(f"    edge fraction surviving  sum_{{k>=5}} p_k            = {keep:.4f}")
print(f"    contact fraction kept    sum_{{k>=5}} k p_k / sum k p_k = {w_keep/w_all:.4f}")

print()
print("=" * 74)
print("4. PER-NEURON AVERAGES")
print("=" * 74)
dbar = F(E, N)
show("dbar = E/N  (mean in-deg = mean out-deg)", float(dbar), "{:.6f}")
show("S/N (mean contacts received per neuron)", float(F(S, N)), "{:.4f}")
show("N-1  (fan-in if fully connected)", N - 1, "{:,}")
print(f"  -> a neuron talks to {float(dbar):.1f} partners out of {N-1:,} possible")
show("dbar / (N-1)", float(dbar) / (N - 1), "{:.6e}")

print()
print("=" * 74)
print("5. MaleCNS / FlyWire RATIOS")
print("=" * 74)
show("R_N = N/N_flywire", N / N_fw, "{:.10f}")
show("R_S = S/S_flywire", S / S_fw, "{:.10f}")
show("S_flywire per neuron (S_fw/N_fw)", S_fw / N_fw, "{:.4f}")
show("S per neuron MaleCNS (S/N)", S / N, "{:.4f}")
show("ratio of contacts-per-neuron", (S / N) / (S_fw / N_fw), "{:.6f}")
print("  (E_flywire NOT supplied by the fragment -> left unknown; no value invented)")

print()
print("=" * 74)
print("6. STORAGE")
print("=" * 74)
GB = 1024 ** 3
dense_f32 = 4 * N * N
csr = 4 * (E + N + 1) + 4 * E      # float32 values (E+N+1) + int32 col indices (E)
show("dense float32 bytes = 4*N^2", dense_f32, "{:,}")
show("dense float32 [GiB] (/2^30)", dense_f32 / GB, "{:.4f}")
show("dense float32 [GB] (/1e9)", dense_f32 / 1e9, "{:.4f}")
show("dense float32 [TB] (/1e12)", dense_f32 / 1e12, "{:.6f}")
show("CSR bytes = 4(E+N+1) + 4E", csr, "{:,}")
show("CSR [GiB]", csr / GB, "{:.6f}")
show("dense / sparse ratio", dense_f32 / csr, "{:.2f}")
show("sparse / dense", csr / dense_f32, "{:.6e}")
show("CSR row-pointer share of bytes", 4 * (N + 1) / csr, "{:.6e}")
print(f"  -> dense float32 is ~{dense_f32/GB:,.0f} GiB : ABSOLUTELY FORBIDDEN")
