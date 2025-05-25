"""
Blockchain Service for Certificate Verification

This module provides a simplified blockchain implementation for certificate verification.
In a production environment, this would be replaced with a real blockchain integration
like Ethereum, Hyperledger, or a specialized blockchain service.
"""

import hashlib
import json
import time
import os
import uuid
from datetime import datetime

# Path to store blockchain data
BLOCKCHAIN_DIR = os.path.join(os.path.dirname(__file__), 'data', 'blockchain')

# Ensure blockchain directory exists
os.makedirs(BLOCKCHAIN_DIR, exist_ok=True)

class Block:
    """Represents a block in the blockchain"""
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        """Calculate SHA-256 hash of the block"""
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)
        
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty):
        """Mine a block (simplified proof of work)"""
        target = '0' * difficulty
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        
        print(f"Block mined: {self.hash}")
        return self.hash

class Blockchain:
    """Simple blockchain implementation for certificate verification"""
    def __init__(self):
        self.chain = []
        self.difficulty = 2  # Simplified difficulty for demo
        self.load_chain()
        
        # Create genesis block if chain is empty
        if len(self.chain) == 0:
            self.create_genesis_block()
    
    def create_genesis_block(self):
        """Create the first block in the chain"""
        genesis_block = Block(0, str(datetime.now()), {
            'message': 'Genesis Block',
            'system': 'AEK NOC System Blockchain'
        }, '0')
        
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
        self.save_chain()
    
    def get_latest_block(self):
        """Get the most recent block in the chain"""
        return self.chain[-1]
    
    def add_block(self, data):
        """Add a new block to the chain"""
        previous_block = self.get_latest_block()
        new_index = previous_block.index + 1
        new_block = Block(new_index, str(datetime.now()), data, previous_block.hash)
        new_block.mine_block(self.difficulty)
        
        self.chain.append(new_block)
        self.save_chain()
        
        return new_block
    
    def is_chain_valid(self):
        """Validate the integrity of the blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Check if hash is valid
            if current_block.hash != current_block.calculate_hash():
                return False
            
            # Check if previous hash reference is valid
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True
    
    def save_chain(self):
        """Save blockchain to disk"""
        chain_data = []
        
        for block in self.chain:
            chain_data.append({
                'index': block.index,
                'timestamp': block.timestamp,
                'data': block.data,
                'previous_hash': block.previous_hash,
                'nonce': block.nonce,
                'hash': block.hash
            })
        
        with open(os.path.join(BLOCKCHAIN_DIR, 'blockchain.json'), 'w') as f:
            json.dump(chain_data, f, indent=4)
    
    def load_chain(self):
        """Load blockchain from disk"""
        try:
            blockchain_file = os.path.join(BLOCKCHAIN_DIR, 'blockchain.json')
            
            if not os.path.exists(blockchain_file):
                return
            
            with open(blockchain_file, 'r') as f:
                chain_data = json.load(f)
            
            self.chain = []
            
            for block_data in chain_data:
                block = Block(
                    block_data['index'],
                    block_data['timestamp'],
                    block_data['data'],
                    block_data['previous_hash']
                )
                block.nonce = block_data['nonce']
                block.hash = block_data['hash']
                self.chain.append(block)
        except Exception as e:
            print(f"Error loading blockchain: {str(e)}")
            self.chain = []

# Singleton instance
_blockchain = None

def get_blockchain():
    """Get the blockchain instance"""
    global _blockchain
    
    if _blockchain is None:
        _blockchain = Blockchain()
    
    return _blockchain

def store_certificate(certificate_data):
    """Store a certificate on the blockchain"""
    blockchain = get_blockchain()
    
    # Generate a unique transaction ID
    transaction_id = str(uuid.uuid4())
    
    # Add transaction metadata
    block_data = {
        'transaction_id': transaction_id,
        'certificate_data': certificate_data,
        'timestamp': str(datetime.now())
    }
    
    # Add to blockchain
    block = blockchain.add_block(block_data)
    
    return transaction_id

def verify_certificate(certificate_hash):
    """Verify a certificate on the blockchain"""
    blockchain = get_blockchain()
    
    # Search for certificate in blockchain
    for block in blockchain.chain:
        if 'certificate_data' in block.data and 'certificate_hash' in block.data['certificate_data']:
            if block.data['certificate_data']['certificate_hash'] == certificate_hash:
                return {
                    'verified': True,
                    'block_index': block.index,
                    'transaction_id': block.data.get('transaction_id'),
                    'timestamp': block.timestamp,
                    'certificate_data': block.data['certificate_data']
                }
    
    return {'verified': False}

def generate_certificate_hash(application_id, business_name, issue_date):
    """Generate a unique hash for a certificate"""
    data = f"{application_id}:{business_name}:{issue_date}:{uuid.uuid4()}"
    return hashlib.sha256(data.encode()).hexdigest()
