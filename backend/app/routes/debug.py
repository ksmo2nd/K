"""
Debug API Routes for testing service functionality
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..services.session_service import SessionService
from ..services.esim_service import ESIMService
from ..core.database import get_supabase_client

router = APIRouter()
session_service = SessionService()
esim_service = ESIMService()


@router.get("/debug/test-sessions")
async def test_sessions():
    """Test if session service is working"""
    try:
        sessions = await session_service.get_available_sessions()
        return {
            "status": "success",
            "sessions_count": len(sessions),
            "sessions": sessions[:3],  # First 3 sessions
            "pricing_config": session_service.pricing
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }


@router.get("/debug/test-esim")
async def test_esim():
    """Test if eSIM service is working"""
    try:
        # Test eSIM generation for a dummy user
        test_user_id = "test-user-123"
        esim = await esim_service.provision_esim(test_user_id, 1024)  # 1GB
        
        return {
            "status": "success",
            "esim_generated": True,
            "iccid": esim.get('iccid'),
            "status_field": esim.get('status'),
            "has_activation_code": bool(esim.get('activation_code'))
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }


@router.get("/debug/test-database")
async def test_database():
    """Test if database connection is working"""
    try:
        supabase = get_supabase_client()
        
        # Test basic operations
        tests = {}
        
        # Test users table
        try:
            response = supabase.table('users').select('id').limit(1).execute()
            tests['users_table'] = "accessible"
        except Exception as e:
            tests['users_table'] = f"error: {str(e)}"
        
        # Test esims table
        try:
            response = supabase.table('esims').select('id').limit(1).execute()
            tests['esims_table'] = "accessible"
        except Exception as e:
            tests['esims_table'] = f"error: {str(e)}"
        
        # Test internet_sessions table
        try:
            response = supabase.table('internet_sessions').select('id').limit(1).execute()
            tests['sessions_table'] = "accessible"
        except Exception as e:
            tests['sessions_table'] = f"error: {str(e)}"
        
        # Test data_packs table
        try:
            response = supabase.table('data_packs').select('id').limit(1).execute()
            tests['data_packs_table'] = "accessible"
        except Exception as e:
            tests['data_packs_table'] = f"error: {str(e)}"
        
        return {
            "status": "success",
            "database_connected": True,
            "table_tests": tests
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }


@router.get("/debug/full-test")
async def full_test():
    """Run all tests"""
    try:
        results = {}
        
        # Test sessions
        session_test = await test_sessions()
        results['sessions'] = session_test
        
        # Test database
        db_test = await test_database()
        results['database'] = db_test
        
        # Test eSIM (only if database works)
        if db_test.get('status') == 'success':
            esim_test = await test_esim()
            results['esim'] = esim_test
        else:
            results['esim'] = {"status": "skipped", "reason": "database not working"}
        
        return {
            "status": "completed",
            "timestamp": "2025-08-26T09:30:00Z",
            "results": results
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }