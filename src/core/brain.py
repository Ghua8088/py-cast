import json
import time
from pathlib import Path
from typing import Dict, List, Optional

class Brain:
    """
    The 'Stream Perceptron' Brain.
    Treats user life as a series of feature signals.
    Raw data is discarded; only the 'Mathematical Entropy' (weights) is kept.
    """
    def __init__(self, bite_instance):
        self.bite = bite_instance
        self.state_path = self.bite.config_dir / "brain_weights.json"
        
        # State: { item_id: { feature_key: weight_value } }
        self.weights = self._load_state()
        self.learning_rate = 0.2
        self.decay_factor = 0.999 # Habit fading (Entropy)
        
    def _load_state(self) -> Dict:
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text())
            except:
                return {}
        return {}
        
    def _save_state(self):
        try:
            self.state_path.write_text(json.dumps(self.weights))
        except:
            pass

    def _get_active_features(self) -> List[str]:
        """Converts current environment into a set of 'Signals'."""
        ctx = self.bite.active_context
        proc = ctx.get("process", "unknown") if ctx else "unknown"
        
        hour = time.localtime().tm_hour
        period = "night"
        if 5 <= hour < 12: period = "morning"
        elif 12 <= hour < 17: period = "afternoon"
        elif 17 <= hour < 21: period = "evening"
        
        return [f"ctx:{proc}", f"time:{period}", "bias:global"]

    def record_event(self, item_id: str):
        """Imbibes the event into the internal weights and discards raw data."""
        features = self._get_active_features()
        now = time.time()
        
        if item_id not in self.weights:
            self.weights[item_id] = {}
            
        target_weights = self.weights[item_id]
        
        # 1. Update Weights (The 'Learning' pulse)
        for f in features:
            current = target_weights.get(f, 0.0)
            # We add the learning rate to strengthen the connection
            target_weights[f] = current + self.learning_rate
            
        # 2. Competitive Normalization & Entropy ( Habit Fading)
        # We apply a global decay to ALL weights for this item to keep it stable
        for f in target_weights:
            target_weights[f] *= self.decay_factor
            
        # 3. Discard raw data immediately. 
        # The 'event' is now just a shift in the float values.
        
        # Periodic save
        if int(now) % 5 == 0:
            self._save_state()

    def predict(self) -> List[Dict]:
        """
        Calculates the activation energy for all known items 
        based on the current signal stream.
        """
        features = self._get_active_features()
        predictions = []
        
        for item_id, item_weights in self.weights.items():
            # In a Perceptron, score = Sum(weight * input)
            # Since inputs are binary signals (1 or 0), it's just a sum of present weights.
            score = 0.0
            for f in features:
                score += item_weights.get(f, 0.0)
                
            if score > 0.01: # Significance threshold
                predictions.append({"id": item_id, "score": score})
                
        # Sort by 'Activation Energy'
        predictions.sort(key=lambda x: -x["score"])
        return predictions[:8]
