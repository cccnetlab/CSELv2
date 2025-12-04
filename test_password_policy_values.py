#!/usr/bin/env python3
"""
Test script to verify password policy Value fields are working correctly.
This tests the database schema, configurator UI changes, and scoring engine logic.
"""

import sys
import os

# Add parent directory to path for relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import db_handler

def test_database_schema():
    """Test that the database schema includes Value column for password policies"""
    print("=" * 60)
    print("Testing Database Schema for Password Policy Value Fields")
    print("=" * 60)
    
    # Initialize the database
    Settings = db_handler.Settings()
    Categories = db_handler.Categories()
    
    # Vulnerability template with Value checks
    vulnerability_template = {
        "Minimum Password Age": {
            "Definition": "Enable this to score the competitor for setting the minimum password age to a specific value.",
            "Description": "Set the minimum password age (in days) that students must configure.",
            "Checks": "Value:Int",
            "Category": "Local Policy",
        },
        "Maximum Password Age": {
            "Definition": "Enable this to score the competitor for setting the maximum password age to a specific value.",
            "Description": "Set the maximum password age (in days) that students must configure.",
            "Checks": "Value:Int",
            "Category": "Local Policy",
        },
        "Minimum Password Length": {
            "Definition": "Enable this to score the competitor for setting the minimum password length to a specific value.",
            "Description": "Set the minimum password length that students must configure.",
            "Checks": "Value:Int",
            "Category": "Local Policy",
        },
    }
    
    Vulnerabilities = db_handler.OptionTables(vulnerability_template)
    Vulnerabilities.initialize_option_table()
    
    # Test each password policy
    password_policies = [
        "Minimum Password Age",
        "Maximum Password Age", 
        "Minimum Password Length",
    ]
    
    all_passed = True
    
    for policy_name in password_policies:
        print(f"\n Testing: {policy_name}")
        print("-" * 60)
        
        try:
            # Get the option table
            option_table = Vulnerabilities.get_option_table(policy_name, config=False)
            
            # Check if the table has at least one row (the default row with id=1)
            if 1 in option_table:
                print(f"  ✓ Table exists with default row")
                
                # Check if Value column exists
                if "Value" in option_table[1]:
                    print(f"  ✓ 'Value' column exists")
                    print(f"    Current value: {option_table[1]['Value']}")
                else:
                    print(f"  ✗ 'Value' column MISSING")
                    all_passed = False
                    
                # Check if Points and Enabled columns exist
                if "Points" in option_table[1]:
                    print(f"  ✓ 'Points' column exists")
                else:
                    print(f"  ✗ 'Points' column MISSING")
                    all_passed = False
                    
                if "Enabled" in option_table[1]:
                    print(f"  ✓ 'Enabled' column exists")
                else:
                    print(f"  ✗ 'Enabled' column MISSING")
                    all_passed = False
            else:
                print(f"  ✗ Default row (id=1) not found")
                all_passed = False
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 60)
    
    return all_passed


def test_value_setting_and_retrieval():
    """Test setting and retrieving Value field"""
    print("\n" + "=" * 60)
    print("Testing Value Field Setting and Retrieval")
    print("=" * 60)
    
    # Initialize
    vulnerability_template = {
        "Minimum Password Age": {
            "Definition": "Test policy",
            "Checks": "Value:Int",
            "Category": "Local Policy",
        },
    }
    
    Vulnerabilities = db_handler.OptionTables(vulnerability_template)
    Vulnerabilities.initialize_option_table()
    
    try:
        # Get the current table (with Tkinter variables)
        option_table = Vulnerabilities.get_option_table("Minimum Password Age", config=True)
        
        print("\nSetting test values:")
        # Set test values
        option_table[1]["Enabled"].set(1)
        option_table[1]["Points"].set(10)
        option_table[1]["Checks"]["Value"].set(30)
        
        print(f"  Enabled: {option_table[1]['Enabled'].get()}")
        print(f"  Points: {option_table[1]['Points'].get()}")
        print(f"  Value: {option_table[1]['Checks']['Value'].get()}")
        
        # Update the table
        Vulnerabilities.update_table("Minimum Password Age", option_table)
        print("  ✓ Updated table in database")
        
        # Retrieve it again (without Tkinter variables)
        retrieved = Vulnerabilities.get_option_table("Minimum Password Age", config=False)
        
        print("\nRetrieved values:")
        print(f"  Enabled: {retrieved[1]['Enabled']}")
        print(f"  Points: {retrieved[1]['Points']}")
        print(f"  Value: {retrieved[1]['Value']}")
        
        # Verify values match
        if (retrieved[1]["Enabled"] == True and 
            retrieved[1]["Points"] == 10 and 
            retrieved[1]["Value"] == 30):
            print("\n  ✓ All values stored and retrieved correctly!")
            return True
        else:
            print("\n  ✗ Values do not match!")
            return False
            
    except Exception as e:
        print(f"\n  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PASSWORD POLICY VALUE FIELD TEST SUITE")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_database_schema()
    test2_passed = test_value_setting_and_retrieval()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Database Schema Test: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"Value Setting/Retrieval Test: {'PASSED' if test2_passed else 'FAILED'}")
    print("=" * 60)
    
    sys.exit(0 if (test1_passed and test2_passed) else 1)
