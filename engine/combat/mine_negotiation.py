"""
FILE: engine/combat/mine_negotiation.py
ROLE: The "Explosive Expert".

DESCRIPTION:
This module handles casualty calculations when units enter minefields.
It uses a Poisson distribution to simulate realistic variance in casualties.
"""
import math
import random

class MineNegotiation:
    @staticmethod
    def negotiate_minefield(unit, obstacle_data):
        """
        Calculates casualties for a unit entering a minefield.
        
        Args:
            unit: BaseEntity object.
            obstacle_data: Dict containing mine properties (e.g., density, damage).
            
        Returns:
            int: Number of casualties.
        """
        # 1. READ CONFIG
        current_personnel = int(unit.get_attribute("personnel", 100))
        density = float(obstacle_data.get("density", 0.5))
        base_damage = float(obstacle_data.get("value", 10)) # Base 'lethality'
        
        # 2. LETHALITY CALCULATION
        # λ = density * base_damage
        lam = density * base_damage
        lam = max(lam, 0.5)
        
        # 3. POISSON SAMPLING
        casualties = MineNegotiation._poisson_sample(lam)
        
        # 4. CLAMP
        casualties = min(casualties, current_personnel)
        
        return casualties

    @staticmethod
    def _poisson_sample(lam):
        """
        Sample from a Poisson distribution.
        - Uses Knuth's algorithm for small lambda (lam < 30).
        - Uses Gaussian approximation for large lambda (lam >= 30).
        Realistic variance centered around λ.
        """
        if lam < 30:
            # Knuth's algorithm
            L = math.exp(-lam)
            k = 0
            p = 1.0
            while p > L:
                k += 1
                p *= random.random()
            return max(0, k - 1)
        else:
            # Gaussian approximation: Poisson(L) ~ Normal(L, sqrt(L))
            # math.sqrt(lam) is the standard deviation.
            sample = random.gauss(lam, math.sqrt(lam))
            return max(0, int(round(sample)))
