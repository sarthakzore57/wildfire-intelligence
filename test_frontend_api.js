// Test script to check frontend API configuration
const axios = require('axios');

// Define the backend API URL
const apiUrl = 'http://localhost:8000/api/v1';

// Function to test login
async function testLogin() {
  console.log('Testing login endpoint...');
  try {
    const response = await axios.post(
      `${apiUrl}/auth/login/access-token`,
      new URLSearchParams({
        username: 'admin@forestfire.com',
        password: 'adminpassword'
      }),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      }
    );
    console.log('Login successful!');
    console.log('Response:', JSON.stringify(response.data, null, 2));
    return response.data.access_token;
  } catch (error) {
    console.error('Login failed:');
    if (error.response) {
      console.error('Status:', error.response.status);
      console.error('Data:', error.response.data);
    } else {
      console.error('Error:', error.message);
    }
    return null;
  }
}

// Function to test getting current user with token
async function testGetCurrentUser(token) {
  if (!token) {
    console.log('Skipping user test: No token available');
    return;
  }
  
  console.log('Testing get current user endpoint...');
  try {
    const response = await axios.get(
      `${apiUrl}/users/me`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    console.log('Get user successful!');
    console.log('User data:', JSON.stringify(response.data, null, 2));
  } catch (error) {
    console.error('Get user failed:');
    if (error.response) {
      console.error('Status:', error.response.status);
      console.error('Data:', error.response.data);
    } else {
      console.error('Error:', error.message);
    }
  }
}

// Run tests
async function runTests() {
  console.log('==== Testing Frontend API Configuration ====');
  console.log('Backend API URL:', apiUrl);
  
  // Test login
  const token = await testLogin();
  
  // Test get current user
  await testGetCurrentUser(token);
  
  console.log('==== Tests completed ====');
}

runTests(); 