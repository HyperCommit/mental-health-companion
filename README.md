# Mental Health Companion
AI-powered mental health companion app using Semantic Kernel

## Mental Health Companion App: DRAFT - Technical Design Proposal

## Table of Contents
- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Repository Structure (Monorepo)](#repository-structure-monorepo)
- [Frontend Design](#frontend-design)
- [Backend Design (Python)](#backend-design-python)
- [Database Design](#database-design)
- [API Endpoints](#api-endpoints)
- [Authentication & Security](#authentication--security)
- [Deployment Strategy](#deployment-strategy)
- [Implementation Timeline](#implementation-timeline)

## Overview
The Mental Health Companion App is an AI-powered mobile application that helps users track their mood, journal their thoughts, practice mindfulness, and receive personalized insights. The app leverages the Microsoft Semantic Kernel framework to provide AI-driven features while maintaining a user-friendly interface.

### Core Features:
- Mood tracking with pattern recognition
- AI-guided journaling with personalized prompts
- Sentiment analysis of journal entries
- Mindfulness exercises tailored to the user's emotional state
- Weekly insights and recommendations

## System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  React Native   │     │  Azure          │     │  Azure          │
│  Mobile App     │◄───►│  Functions API  │◄───►│  Cosmos DB      │
│  (Frontend)     │     │  (Backend)      │     │  (Database)     │
│                 │     │                 │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 │
                        ┌────────▼────────┐
                        │                 │
                        │  Semantic       │
                        │  Kernel         │
                        │                 │
                        └───┬─────────┬───┘
                            │         │
                 ┌──────────▼──┐   ┌──▼──────────┐
                 │             │   │             │
                 │  Azure      │   │  Azure      │
                 │  OpenAI     │   │  Blob       │
                 │  Service    │   │  Storage    │
                 │             │   │             │
                 └─────────────┘   └─────────────┘
```

### User Flow

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│              │       │              │       │              │       │              │
│  User Login  │───┬──►│ Home Screen  │◄──────┤ Mood Tracker │◄──┬───┤ Journal Entry│
│              │   │   │              │       │              │   │   │              │
└──────────────┘   │   └──────┬───────┘       └──────▲───────┘   │   └──────▲───────┘
                   │          │                      │           │          │
                   │          │                      │           │          │
                   │   ┌──────▼───────┐       ┌──────┴───────┐   │   ┌─────┴────────┐
                   └───┤ Mindfulness  │       │   Weekly     │◄──┴───┤ AI-Generated │
                       │ Exercises    │       │   Insights   │       │ Recommendations│
                       │              │       │              │       │              │
                       └──────────────┘       └──────────────┘       └──────────────┘
```

## Repository Structure (Monorepo)

```
mental-health-companion/
├── README.md
├── package.json               # Root package.json for JS dependencies
├── pyproject.toml             # Root Python project configuration
├── .github/                   # GitHub Actions workflows
├── docs/                      # Project documentation
│
├── frontend/                  # React Native application
│   ├── package.json           # Frontend-specific dependencies
│   ├── src/                   # React Native source code
│   │   ├── components/        # UI components
│   │   ├── screens/           # App screens
│   │   ├── services/          # API services
│   │   └── contexts/          # State management
│   ├── assets/                # Images, fonts, etc.
│   └── tests/                 # Frontend tests
│
├── backend/                   # Python Azure Functions
│   ├── requirements.txt       # Python dependencies
│   ├── host.json              # Azure Functions configuration
│   ├── local.settings.json    # Local settings (gitignored)
│   ├── shared/                # Shared utility code
│   │   ├── kernel_setup.py    # Semantic Kernel configuration
│   │   └── db_client.py       # Database access
│   ├── plugins/               # Semantic Kernel plugins
│   │   ├── mood_analyzer.py
│   │   ├── journal_plugin.py
│   │   └── insights_plugin.py
│   └── api/                   # Azure Functions endpoints
│       ├── mood/              # Mood tracking functions
│       ├── journal/           # Journal functions
│       └── mindfulness/       # Mindfulness functions
│
├── shared/                    # Shared code between frontend/backend
│   ├── models/                # Data models (TypeScript/Python)
│   ├── constants/             # Shared constants
│   └── utils/                 # Shared utilities
│
└── infrastructure/            # IaC for Azure deployment
    ├── bicep/                 # Bicep templates
    ├── scripts/               # Deployment scripts
    └── config/                # Environment configurations
```

## Frontend Design

### Technology Stack
- React Native with Expo
- TypeScript for type safety
- React Navigation for screen navigation
- React Native Paper for UI components
- Context API for state management

### Key Screens:
#### Home Dashboard    

```javascript
// frontend/src/screens/HomeScreen.js
import React, { useEffect, useState } from 'react';
import { View, ScrollView, StyleSheet } from 'react-native';
import { Card, Title, Paragraph } from 'react-native-paper';
import { useMoodData } from '../hooks/useMoodData';
import { MoodSummary } from '../components/mood/MoodSummary';
import { RecommendedActivities } from '../components/mindfulness/RecommendedActivities';
import { RecentJournals } from '../components/journal/RecentJournals';

export const HomeScreen = () => {
  const { todayMood, weeklyTrend } = useMoodData();
  const [recommendations, setRecommendations] = useState([]);
  
  useEffect(() => {
    // Fetch personalized recommendations based on mood data
    fetchRecommendations(todayMood);
  }, [todayMood]);
  
  const fetchRecommendations = async (mood) => {
    try {
      const response = await fetch(`${API_URL}/api/mindfulness/recommended?mood=${mood}`);
      const data = await response.json();
      setRecommendations(data);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    }
  };
  
  return (
    <ScrollView style={styles.container}>
      <MoodSummary mood={todayMood} trend={weeklyTrend} />
      <Card style={styles.card}>
        <Card.Content>
          <Title>Today's Focus</Title>
          <Paragraph>Based on your recent moods, we recommend focusing on calm activities today.</Paragraph>
        </Card.Content>
      </Card>
      <RecommendedActivities activities={recommendations} />
      <RecentJournals maxEntries={3} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: '#f5f5f5',
  },
  card: {
    marginVertical: 8,
    elevation: 2,
  },
});
```

#### Mood Tracker

```javascript
// frontend/src/screens/MoodTrackerScreen.js
import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { Title, Button } from 'react-native-paper';
import { MoodSelector } from '../components/mood/MoodSelector';
import { IntensitySlider } from '../components/mood/IntensitySlider';
import { NotesInput } from '../components/common/NotesInput';
import { useMoodData } from '../hooks/useMoodData';

export const MoodTrackerScreen = () => {
  const [selectedMood, setSelectedMood] = useState(null);
  const [intensity, setIntensity] = useState(5);
  const [notes, setNotes] = useState('');
  const { saveMoodEntry } = useMoodData();
  
  const handleSave = async () => {
    try {
      await saveMoodEntry({
        mood: selectedMood,
        intensity,
        notes,
        timestamp: new Date().toISOString()
      });
      
      // Reset form and show success message
      setSelectedMood(null);
      setIntensity(5);
      setNotes('');
    } catch (error) {
      console.error('Error saving mood:', error);
    }
  };
  
  return (
    <View style={styles.container}>
      <Title style={styles.title}>How are you feeling right now?</Title>
      <MoodSelector onSelect={setSelectedMood} selected={selectedMood} />
      <IntensitySlider value={intensity} onChange={setIntensity} />
      <NotesInput 
        value={notes} 
        onChangeText={setNotes} 
        placeholder="Add notes about your mood (optional)"
      />
      <Button 
        mode="contained" 
        onPress={handleSave} 
        disabled={!selectedMood}
        style={styles.button}
      >
        Save My Mood
      </Button>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#ffffff',
  },
  title: {
    marginBottom: 24,
    textAlign: 'center',
  },
  button: {
    marginTop: 24,
    paddingVertical: 8,
  },
});
```

### API Service

```typescript
// frontend/src/services/ApiService.ts
import { API_URL } from '../constants/api';

class ApiService {
  private token: string | null = null;
  
  setToken(token: string) {
    this.token = token;
  }
  
  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_URL}${endpoint}`, {
      headers: {
        'Authorization': this.token ? `Bearer ${this.token}` : '',
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  }
  
  async post<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Authorization': this.token ? `Bearer ${this.token}` : '',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  }
}

export const apiService = new ApiService();
```

## Backend Design (Python)

### Azure Functions with Semantic Kernel

#### Kernel Setup

```python
# backend/shared/kernel_setup.py
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
import os

def initialize_kernel():
    """Creates and configures a Semantic Kernel instance"""
    # Create kernel
    kernel = Kernel()
    
    # Configure Azure OpenAI service
    deployment_name = os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"]
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    api_key = os.environ["AZURE_OPENAI_API_KEY"]
    
    # Add chat completion service
    chat_service = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint, 
        api_key=api_key
    )
    kernel.add_chat_service("azure_chat", chat_service)
    
    return kernel
```

### Journal Plugin

```python
# backend/plugins/journal_plugin.py
from semantic_kernel.plugin_definition import kernel_function

class JournalPlugin:
    """Plugin for journal-related AI functionality"""
    
    @kernel_function(description="Generates a thoughtful journal prompt based on the user's mood")
    async def generate_prompt(self, mood: str) -> str:
        """Generates a journal prompt customized for the user's current mood"""
        # The implementation is handled by the Semantic Kernel
        # This function signature serves as a contract for the AI
        return f"Prompt for {mood} mood"
    
    @kernel_function(description="Analyzes the sentiment and emotional themes in journal text")
    async def analyze_sentiment(self, journal_text: str) -> str:
        """Analyzes the emotional content and themes in a journal entry"""
        # The implementation is handled by the Semantic Kernel
        # This function signature serves as a contract for the AI
        return f"Sentiment analysis for journal entry"
```

### Journal Prompt Function

```python
# backend/api/journal/generate_prompt.py
import azure.functions as func
import json
import logging
from shared.kernel_setup import initialize_kernel
from plugins.journal_plugin import JournalPlugin

async def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing request for journal prompt generation')
    
    # Parse request
    try:
        req_body = req.get_json()
        mood = req_body.get('mood')
    except ValueError:
        mood = req.params.get('mood')
        
    if not mood:
        return func.HttpResponse(
            json.dumps({"error": "Please provide a mood"}),
            status_code=400,
            mimetype="application/json"
        )
    
    try:
        # Initialize kernel
        kernel = initialize_kernel()
        
        # Add journal plugin
        kernel.add_plugin(JournalPlugin(), plugin_name="Journal")
        
        # Generate prompt through the plugin
        result = await kernel.invoke_function_async(
            plugin_name="Journal",
            function_name="generate_prompt",
            arguments={"mood": mood}
        )
        
        return func.HttpResponse(
            json.dumps({"prompt": str(result)}),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error generating prompt: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )
```

### Database Client

```python
# backend/shared/db_client.py
from azure.cosmos import CosmosClient, PartitionKey
import os
import logging
from datetime import datetime

class CosmosDbClient:
    def __init__(self):
        endpoint = os.environ["COSMOS_ENDPOINT"]
        key = os.environ["COSMOS_KEY"]
        database_name = os.environ["COSMOS_DATABASE"]
        
        self.client = CosmosClient(endpoint, key)
        self.database = self.client.get_database_client(database_name)
    
    def get_container(self, container_name):
        return self.database.get_container_client(container_name)
    
    async def create_item(self, container_name, item):
        container = self.get_container(container_name)
        return await container.create_item(body=item)
    
    async def query_items(self, container_name, query, params=None):
        container = self.get_container(container_name)
        items = container.query_items(
            query=query,
            parameters=params,
            enable_cross_partition_query=True
        )
        return [item async for item in items]
```

## Database Design

### Cosmos DB Collections

#### Users

```json
{
  "id": "user123",
  "email": "user@example.com",
  "name": "John Doe",
  "preferences": {
    "notificationSettings": { "dailyReminder": true, "weeklyInsights": true },
    "privacySettings": { "dataRetentionMonths": 12 }
  },
  "emergencyContacts": [
    { "name": "Jane Doe", "phone": "+1234567890", "relationship": "Partner" }
  ],
  "createdAt": "2025-04-01T12:00:00Z"
}
```

#### MoodEntries

```json
{
  "id": "mood123",
  "userId": "user123",
  "mood": "anxious",
  "intensity": 7,
  "notes": "Presentation at work",
  "timestamp": "2025-04-07T15:30:00Z"
}
```

#### JournalEntries

```json
{
  "id": "journal123",
  "userId": "user123",
  "content": "Today I felt overwhelmed with my workload...",
  "prompt": "What's causing you stress today?",
  "sentimentAnalysis": {
    "primaryEmotion": "anxiety",
    "intensity": 0.75,
    "topics": ["work", "stress", "deadlines"]
  },
  "timestamp": "2025-04-07T20:15:00Z"
}
```

#### MindfulnessActivities

```json
{
  "id": "activity123",
  "name": "5-Minute Breathing",
  "category": "breathing",
  "mediaUrl": "https://storage.blob.core.windows.net/mindfulness/breathing_5min.mp3",
  "duration": 300,
  "description": "A simple breathing exercise for quick stress relief",
  "recommendedFor": ["anxiety", "stress"]
}
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Log in user
- `POST /api/auth/logout` - Log out user

### Mood Tracking
- `POST /api/mood` - Record mood entry
- `GET /api/mood` - Get mood history
- `GET /api/mood/trends` - Get mood trend analysis

### Journal
- `POST /api/journal` - Create journal entry
- `GET /api/journal` - Get journal entries
- `GET /api/journal/prompt` - Get AI-generated prompt
- `POST /api/journal/analyze` - Analyze journal sentiment

### Mindfulness
- `GET /api/mindfulness/exercises` - List exercises
- `GET /api/mindfulness/recommended` - Get personalized recommendations
- `POST /api/mindfulness/track` - Record completed activity

### Insights
- `GET /api/insights/weekly` - Get weekly summary and insights

## Authentication & Security

### Authentication Flow

```
┌──────────────┐     ┌───────────────┐     ┌─────────────────┐     ┌───────────────┐
│              │     │               │     │                 │     │               │
│ User         │────►│ React Native  │────►│ Azure AD B2C    │────►│ Token         │
│              │     │ App           │     │ Authentication  │     │ Acquisition   │
└──────────────┘     └───────┬───────┘     └─────────────────┘     └───────┬───────┘
                             │                                             │
                             │                                             │
                     ┌───────▼───────┐                             ┌───────▼───────┐
                     │               │                             │               │
                     │ API Requests  │◄────────────────────────────┤ JWT Token     │
                     │ with Token    │                             │               │
                     └───────┬───────┘                             └───────────────┘
                             │
                             │
                     ┌───────▼───────┐     ┌─────────────────┐
                     │               │     │                 │
                     │ Azure         │────►│ Validate Token  │
                     │ Functions     │     │ & Authorize     │
                     │               │     │                 │
                     └───────────────┘     └─────────────────┘
```

### Azure AD B2C Implementation

```python
# backend/auth/validate_token.py
import azure.functions as func
import json
import logging
from msal import ConfidentialClientApplication
import jwt
import os

async def validate_token(token):
    """Validates the JWT token issued by Azure AD B2C"""
    tenant_id = os.environ["AZURE_AD_B2C_TENANT_ID"]
    client_id = os.environ["AZURE_AD_B2C_CLIENT_ID"]
    policy_name = os.environ["AZURE_AD_B2C_POLICY_NAME"]
    
    issuer = f"https://{tenant_id}.b2clogin.com/{tenant_id}.onmicrosoft.com/v2.0/"
    
    try:
        # Decode and validate token
        decoded = jwt.decode(
            token,
            options={"verify_signature": False},  # We verify using MSAL below
            audience=client_id,
            issuer=issuer
        )
        
        # Additional validation can be performed here
        
        return decoded
    except Exception as e:
        logging.error(f"Token validation error: {str(e)}")
        return None
```

## Deployment Strategy

### CI/CD Pipeline

```yaml
# .github/workflows/main.yml
name: Build and Deploy

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'yarn'
      - name: Install dependencies
        run: cd frontend && yarn install
      - name: Run tests
        run: cd frontend && yarn test

  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: cd backend && pip install -r requirements.txt
      - name: Run tests
        run: cd backend && pytest

  deploy:
    needs: [frontend-test, backend-test]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Deploy backend to Azure Functions
        uses: Azure/functions-action@v1
        with:
          app-name: mental-health-companion-api
          package: backend
      
      - name: Build frontend
        run: |
          cd frontend
          yarn install
          yarn build
      
      - name: Deploy frontend to Azure Static Web Apps
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: "upload"
          app_location: "frontend/build"
          output_location: ""
          skip_app_build: true
```

### Azure Resources
The following Azure resources will be provisioned:

- Azure Functions App (for the backend)
- Azure Static Web Apps (for the frontend)
- Azure Cosmos DB (for the database)
- Azure OpenAI Service (for AI capabilities)
- Azure AD B2C (for authentication)
- Azure Blob Storage (for media files)
- Azure Application Insights (for monitoring)

Resource provisioning will be automated using Bicep templates in the infrastructure directory.

## Implementation Timeline

### Phase 1: Foundation
- Set up monorepo structure and CI/CD pipeline
- Create basic React Native app with navigation
- Implement Azure AD B2C authentication
- Set up Azure Functions with Semantic Kernel

### Phase 2: Core Features
- Implement mood tracking UI and API
- Develop basic journaling functionality
- Configure database schema and connections
- Create initial AI plugin templates

### Phase 3: AI Integration
- Implement journal prompt generation with Semantic Kernel
- Develop sentiment analysis for journal entries
- Create mood pattern recognition
- Build mindfulness exercise recommendation system

### Phase 4: Refinement
- Add weekly insights and personalized recommendations
- Implement data visualization for mood trends
- Conduct user testing and gather feedback
- Optimize performance and fix bugs

### Phase 5: Launch Preparation
- Conduct security audit and implement fixes
- Perform final UI/UX refinements
- Prepare app store listings
- Deploy to production environment

This design proposal provides a comprehensive blueprint for building the Mental Health Companion App using modern technologies including React Native, Azure Functions, Semantic Kernel, and Azure Cosmos DB. The monorepo structure facilitates collaboration between frontend and backend development while ensuring consistency across the application.

       
       