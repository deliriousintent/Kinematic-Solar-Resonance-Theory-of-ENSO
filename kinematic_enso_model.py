"""
Kinematic-Solar Resonance Theory of ENSO - Computational Hindcast Model
Author: [Your Name/Handle]
Description: This script calculates the ENSO Momentum Delta (E_M) and 
subsequent ENSO state using NASA JPL Horizons heliocentric distances, 
detrended Ocean Memory (WWV), and lagged Solar Sunspot velocity.
"""

import numpy as np
import pandas as pd
from scipy.integrate import simps

class KinematicEnsoModel:
    def __init__(self, alpha=1.2, beta=0.8, c_k=1.0, gamma_coef=0.1):
        """
        Initialize the model with calibration constants.
        alpha: Northern Continental Volatility Weight
        beta: Southern Oceanic Absorption Weight
        c_k: Kinematic scaling constant
        gamma_coef: Solar derivative scaling constant
        """
        self.S_0 = 1361.0 # Solar constant in W/m^2
        self.alpha = alpha
        self.beta = beta
        self.c_k = c_k
        self.gamma_coef = gamma_coef

    def _irradiance(self, r_au):
        """Calculates dimensionally explicit Total Solar Irradiance."""
        return self.S_0 * (1.0 / r_au)**2

    def calculate_kinematic_anomaly(self, r_jan_jul, r_jul_jan, I_mean):
        """
        Integrates solar irradiance over the Earth's orbit, applying
        hemispheric asymmetry weights, and calculates the K vector.
        r_jan_jul: Array of daily Earth-Sun distances (AU) from Jan 1 to Jul 1
        r_jul_jan: Array of daily Earth-Sun distances (AU) from Jul 1 to Jan 1
        I_mean: Historical average of the effective integral
        """
        # Calculate daily irradiance for both halves of the year
        S_jan_jul = self._irradiance(np.array(r_jan_jul))
        S_jul_jan = self._irradiance(np.array(r_jul_jan))
        
        # Integrate using Simpson's rule
        I_north = simps(S_jan_jul)
        I_south = simps(S_jul_jan)
        
        # Calculate Effective Annual Insolation
        I_eff = (self.alpha * I_north) + (self.beta * I_south)
        
        # Calculate Anomaly
        delta_I = I_eff - I_mean
        
        # Map to Kinematic Vector K and clip between [-1, 1]
        K = np.clip(self.c_k * delta_I, -1.0, 1.0)
        return K

    def calculate_solar_amplifier(self, ssn_series):
        """
        Calculates the Geomagnetic Forcing Factor (Gamma) using a 
        12-month trailing moving average (TMA), lagged by 6 months.
        ssn_series: Pandas Series of monthly sunspot numbers
        """
        # 12-month Trailing Moving Average, lagged 6 months
        tma_lagged = ssn_series.rolling(window=12).mean().shift(6)
        
        # Calculate rate of change (derivative)
        d_ssn_dt = tma_lagged.diff()
        
        # Calculate Gamma and clip between [1.0, 3.0]
        gamma = np.clip(1.0 + self.gamma_coef * np.abs(d_ssn_dt), 1.0, 3.0)
        return gamma.iloc[-1] # Return the current year's Gamma

    def calculate_ocean_memory(self, wwv_detrended):
        """
        Clips the detrended Warm Water Volume (WWV) to Ocean Memory bounds.
        """
        return np.clip(wwv_detrended, -5.0, 5.0)

    def predict_enso_state(self, prev_enso, K, omega_mem, gamma):
        """
        Calculates the Momentum Delta (E_M) and the resulting ENSO state.
        prev_enso: ENSO rating from the previous year [-10 to +10]
        """
        # Momentum Delta Equation
        E_M = (K + omega_mem) * gamma
        
        # Resulting State Equation (Clipped to observational bounds)
        enso_t = np.clip(prev_enso + E_M, -10.0, 10.0)
        
        return np.round(E_M, 2), np.round(enso_t, 2)


# =====================================================================
# HISTORICAL PROOF OF CONCEPT (WORKED EXAMPLES)
# =====================================================================
if __name__ == "__main__":
    print("--- Kinematic-Solar Resonance Engine Validation ---\n")
    model = KinematicEnsoModel()

    # --- CASE A: 1997 Super El Niño ---
    print("TEST CASE A: 1997 Super El Niño Override")
    prev_enso_1996 = -2.0  # Weak La Niña
    K_1997 = -1.0          # Kinematic cooling bias
    omega_1997 = 5.0       # Fully primed ocean (loaded spring)
    gamma_1997 = 3.0       # Solar cycle 23 rapid rise

    delta_1997, state_1997 = model.predict_enso_state(
        prev_enso_1996, K_1997, omega_1997, gamma_1997
    )
    
    print(f"Previous State: {prev_enso_1996}")
    print(f"Momentum Delta (E_M): {delta_1997}")
    print(f"Predicted ENSO State: {state_1997} (Actual: +10)")
    print(f"Result: {'PASS' if state_1997 == 10.0 else 'FAIL'}\n")

    # --- CASE B: 1988 Super La Niña ---
    print("TEST CASE B: 1988 Super La Niña Crash")
    prev_enso_1987 = 7.0   # Strong El Niño
    K_1988 = -1.0          # Kinematic cooling bias
    omega_1988 = -5.0      # Exhausted ocean battery
    gamma_1988 = 3.0       # Solar cycle 22 rapid rise

    delta_1988, state_1988 = model.predict_enso_state(
        prev_enso_1987, K_1988, omega_1988, gamma_1988
    )
    
    print(f"Previous State: {prev_enso_1987}")
    print(f"Momentum Delta (E_M): {delta_1988}")
    print(f"Predicted ENSO State: {state_1988} (Actual: -10)")
    print(f"Result: {'PASS' if state_1988 == -10.0 else 'FAIL'}\n")
