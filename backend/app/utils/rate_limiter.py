"""
Rate limiting utility for API requests
"""

import time
from collections import defaultdict, deque
from typing import Dict
from config import settings

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.clients: Dict[str, deque] = defaultdict(deque)
        self.max_requests = settings.RATE_LIMIT_REQUESTS
        self.time_window = settings.RATE_LIMIT_WINDOW
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if client is allowed to make request"""
        now = time.time()
        
        # Get client's request history
        requests = self.clients[client_id]
        
        # Remove old requests outside the time window
        while requests and requests[0] <= now - self.time_window:
            requests.popleft()
        
        # Check if under limit
        if len(requests) < self.max_requests:
            requests.append(now)
            return True
        
        return False
    
    def get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests for client"""
        now = time.time()
        requests = self.clients[client_id]
        
        # Remove old requests
        while requests and requests[0] <= now - self.time_window:
            requests.popleft()
        
        return max(0, self.max_requests - len(requests))
    
    def get_reset_time(self, client_id: str) -> float:
        """Get time when rate limit resets for client"""
        requests = self.clients[client_id]
        if not requests:
            return time.time()
        
        return requests[0] + self.time_window
    
    def clear_client(self, client_id: str):
        """Clear rate limit data for client"""
        if client_id in self.clients:
            del self.clients[client_id]
    
    def cleanup_old_entries(self):
        """Cleanup old entries to prevent memory bloat"""
        now = time.time()
        clients_to_remove = []
        
        for client_id, requests in self.clients.items():
            # Remove old requests
            while requests and requests[0] <= now - self.time_window:
                requests.popleft()
            
            # If no requests left, mark client for removal
            if not requests:
                clients_to_remove.append(client_id)
        
        # Remove empty clients
        for client_id in clients_to_remove:
            del self.clients[client_id]
