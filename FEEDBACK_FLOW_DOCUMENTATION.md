# Complete Feedback Flow Documentation
## Frontend to Backend Training Exercise Feedback System

### Overview
This document traces the complete flow of training exercise submission and feedback generation from the frontend React components through the backend Flask API to the database and back.

---

## 1. FRONTEND INITIATION

### 1.1 User Interface Entry Point
**File**: `frontend/src/components/AIFeedback.jsx`
- **Component**: `AIFeedback`
- **Function**: Renders `AIExerciseBlock` with `blockId="training"`
- **Data Passed**:
  ```javascript
  <AIExerciseBlock
    data={data}
    blockId="training"
    onComplete={handleComplete}
    setFooterActions={setFooterActions}
  />
  ```

### 1.2 Exercise Block Component
**File**: `frontend/src/components/AIExerciseBlock.jsx`
- **Component**: `AIExerciseBlock`
- **Props Received**:
  - `blockId="training"`
  - `data` (exercise data)
  - `onComplete` (callback)
  - `setFooterActions` (UI state setter)

### 1.3 Submit Button Handler
**File**: `frontend/src/components/AIExerciseBlock.jsx`
- **Function**: `handleSubmit` (line ~280)
- **Trigger**: User clicks "Submit Answers" button
- **Preconditions**: All exercises must be answered (`allExercisesAnswered`)

**Data Collected**:
```javascript
const currentAnswers = answersRef.current; // User's answers
const blockToSubmit = currentBlockRef.current || current; // Exercise block data
const actualBlockId = blockToSubmit?.block_id || blockId; // "training" or actual block_id
```

**Exercise Block Data Structure**:
```javascript
const exerciseBlockData = {
    instructions: blockToSubmit?.instructions || "",
    exercises: blockToSubmit?.exercises || [],
    vocabHelp: blockToSubmit?.vocabHelp || [],
    topic: blockToSubmit?.topic || "general",
};
```

---

## 2. FRONTEND API CALL

### 2.1 Training-Specific Submission
**File**: `frontend/src/components/AIExerciseBlock.jsx` (line ~318-331)
- **Condition**: `if (actualBlockId === "training")`
- **Function Called**: `submitTrainingExercise(currentAnswers, exerciseBlockData)`

### 2.2 API Function
**File**: `frontend/src/api.js` (line ~702-723)
- **Function**: `submitTrainingExercise`
- **Endpoint**: `POST /api/ai-exercise/training/submit`
- **Request Body**:
  ```javascript
  {
    "answers": currentAnswers, // User's answers object
    "exercise_block": exerciseBlockData // Exercise metadata
  }
  ```
- **Headers**:
  - `Content-Type: application/json`
  - `credentials: "include"` (includes session cookie)

---

## 3. BACKEND RECEPTION

### 3.1 Training Submission Endpoint
**File**: `backend/src/api/routes/ai/training.py` (line ~247)
- **Route**: `@ai_bp.route("/ai-exercise/training/submit", methods=["POST"])`
- **Function**: `submit_training_exercise()`

### 3.2 Authentication Check
**File**: `backend/src/api/routes/ai/training.py` (line ~340)
- **Function**: `require_user()`
- **Purpose**: Validates user session and returns username
- **Returns**: `username` (string) or raises 401 Unauthorized

### 3.3 Database Query for Exercise Data
**File**: `backend/src/api/routes/ai/training.py` (line ~350-365)
- **Function**: `select_one()`
- **Table**: `ai_user_data`
- **Columns**: `exercises, next_exercises`
- **Where**: `username = ?`
- **Purpose**: Retrieves current exercise data for the user

**Data Flow**:
```python
row = select_one(
    "ai_user_data",
    columns="exercises, next_exercises",
    where="username = ?",
    params=(username,),
)
```

### 3.4 Exercise Data Extraction
**File**: `backend/src/api/routes/ai/training.py` (line ~367-375)
- **Priority**: Check `exercises` column first, fallback to `next_exercises`
- **JSON Parsing**: `json.loads(exercise_data)`
- **Block ID Extraction**:
  ```python
  block_id = exercise_block.get("block_id") or exercise_block.get("id") or "training"
  ```

### 3.5 Delegation to Main Exercise Handler
**File**: `backend/src/api/routes/ai/training.py` (line ~380-390)
- **Function**: `submit_ai_exercise(block_id, data)`
- **Data Passed**:
  - `block_id`: Extracted from exercise data (e.g., "blk0001")
  - `data`: Request data with added `exercise_block`

---

## 4. MAIN EXERCISE EVALUATION

### 4.1 Main Exercise Endpoint
**File**: `backend/src/api/routes/ai/exercise.py` (line ~34)
- **Route**: `@ai_bp.route("/ai-exercise/<block_id>/submit", methods=["POST"])`
- **Function**: `submit_ai_exercise(block_id, data=None)`

### 4.2 Data Parsing
**File**: `backend/src/features/exercise/exercise_evaluation.py`
- **Function**: `parse_submission_data(data)`
- **Purpose**: Extracts exercises, answers, and validates data
- **Returns**: `(exercises, answers, error)`

### 4.3 First Exercise Evaluation
**File**: `backend/src/features/exercise/exercise_evaluation.py`
- **Function**: `evaluate_first_exercise(exercises, answers)`
- **Purpose**: Provides immediate feedback for the first exercise
- **Returns**: `first_result_with_details`

### 4.4 Background Task Initiation
**File**: `backend/src/api/routes/ai/exercise.py` (line ~110-130)
- **Thread**: Background thread for full evaluation
- **Function**: `background_task()`
- **Calls**: `evaluate_remaining_exercises_async()`

### 4.5 Immediate Response
**File**: `backend/src/api/routes/ai/exercise.py` (line ~130-140)
- **Response Structure**:
  ```json
  {
    "block_id": "blk0001",
    "pass": false,
    "summary": {"correct": 0, "total": 3, "mistakes": []},
    "results": immediate_results,
    "streaming": true
  }
  ```

---

## 5. BACKGROUND EVALUATION PROCESS

### 5.1 Async Evaluation Function
**File**: `backend/src/features/exercise/exercise_evaluation.py`
- **Function**: `evaluate_remaining_exercises_async()`
- **Parameters**:
  - `username`: User identifier
  - `block_id`: Exercise block ID
  - `exercises`: Exercise data
  - `answers`: User answers
  - `first_result`: First exercise result
  - `exercise_block`: Exercise metadata

### 5.2 AI Answer Processing
**File**: `backend/src/features/ai/evaluation/exercise_evaluation.py`
- **Function**: `process_ai_answers()`
- **Purpose**: Evaluates all exercises using AI
- **Returns**: Evaluation results with feedback

### 5.3 Database Storage
**File**: `backend/src/features/exercise/exercise_evaluation.py`
- **Table**: `ai_exercise_results`
- **Data Stored**:
  - `block_id`: Exercise block identifier
  - `username`: User identifier
  - `results`: JSON string of evaluation results
  - `summary`: Overall performance summary
  - `ai_feedback`: AI-generated feedback
  - `created_at`: Timestamp

### 5.4 Topic Memory Integration
**File**: `backend/src/features/ai/memory/level_manager.py`
- **Function**: Updates user's topic memory based on performance
- **Purpose**: Tracks learning progress and adjusts difficulty

---

## 6. FRONTEND POLLING FOR RESULTS

### 6.1 Enhanced Results Polling
**File**: `frontend/src/components/AIExerciseBlock.jsx` (line ~431)
- **Function**: `startEnhancedResultsPolling(activityId, blockIdToUse)`
- **Block ID Source**: `apiResult?.block_id || current?.block_id || blockId`

### 6.2 API Call for Results
**File**: `frontend/src/api.js` (line ~843-863)
- **Function**: `getEnhancedResults(blockId)`
- **Endpoint**: `GET /api/ai-exercise/{blockId}/results`
- **Headers**:
  - `Content-Type: application/json`
  - `credentials: "include"`

### 6.3 Polling Logic
**File**: `frontend/src/components/AIExerciseBlock.jsx` (line ~440-530)
- **Interval**: Continuous polling until results are complete
- **Status Check**: `enhancedData.status === "complete"`
- **Progressive Updates**: Updates results as they become available

---

## 7. BACKEND RESULTS ENDPOINT

### 7.1 Results Retrieval
**File**: `backend/src/api/routes/ai/exercise.py` (line ~150)
- **Route**: `@ai_bp.route("/ai-exercise/<block_id>/results", methods=["GET"])`
- **Function**: `get_ai_exercise_results(block_id)`

### 7.2 Database Query
**File**: `backend/src/api/routes/ai/exercise.py` (line ~200-210)
- **Table**: `ai_exercise_results`
- **Query**:
  ```python
  results = select_one(
      "ai_exercise_results",
      columns="*",
      where="block_id = ? AND username = ?",
      params=(block_id, username)
  )
  ```

### 7.3 Response Structure
**File**: `backend/src/api/routes/ai/exercise.py` (line ~210)
- **Response**: JSON object with complete evaluation results
- **Structure**:
  ```json
  {
    "block_id": "blk0001",
    "username": "testuser2",
    "results": [...],
    "summary": {...},
    "ai_feedback": {...},
    "created_at": "2025-08-03T16:52:11"
  }
  ```

---

## 8. FRONTEND RESULT PROCESSING

### 8.1 Enhanced Results Processing
**File**: `frontend/src/components/AIExerciseBlock.jsx` (line ~445-480)
- **Function**: Updates `evaluation` state with detailed feedback
- **Data Structure**:
  ```javascript
  enhancedMap[result.id] = {
    is_correct: result.is_correct,
    correct: result.correct_answer,
    alternatives: result.alternatives || [],
    explanation: result.explanation || "",
    loading: false
  };
  ```

### 8.2 UI Updates
**File**: `frontend/src/components/AIExerciseBlock.jsx`
- **State Updates**:
  - `setEvaluation(enhancedMap)`
  - `setEnhancedResultsLoading(false)`
  - `setPassed(enhancedData.pass)`

### 8.3 Topic Memory Polling
**File**: `frontend/src/components/AIExerciseBlock.jsx` (line ~545)
- **Function**: `pollForTopicMemoryCompletion(activityId)`
- **Purpose**: Monitors background topic memory processing

---

## 9. DATABASE SCHEMA

### 9.1 ai_user_data Table
**Purpose**: Stores user's current and next exercises
**Columns**:
- `username` (TEXT, PRIMARY KEY)
- `exercises` (TEXT) - JSON string of current exercises
- `next_exercises` (TEXT) - JSON string of prefetched exercises

### 9.2 ai_exercise_results Table
**Purpose**: Stores completed exercise evaluations
**Columns**:
- `block_id` (TEXT) - Exercise block identifier
- `username` (TEXT) - User identifier
- `results` (TEXT) - JSON string of evaluation results
- `summary` (TEXT) - JSON string of performance summary
- `ai_feedback` (TEXT) - JSON string of AI feedback
- `created_at` (TEXT) - Timestamp

---

## 10. ERROR HANDLING

### 10.1 Frontend Error Handling
**File**: `frontend/src/components/AIExerciseBlock.jsx`
- **Network Errors**: Continue polling with exponential backoff
- **Timeout Errors**: Show timeout message after 30 seconds
- **API Errors**: Log and display error messages

### 10.2 Backend Error Handling
**File**: `backend/src/api/routes/ai/training.py`
- **Database Errors**: Return 500 with error message
- **Validation Errors**: Return 400 with specific error
- **Authentication Errors**: Return 401 Unauthorized

---

## 11. LOGGING POINTS

### 11.1 Key Log Messages to Monitor
1. **Training Submission**: `"User {username} submitting training exercise"`
2. **Block ID Extraction**: `"Extracted block_id: {block_id} from exercise data"`
3. **Exercise Evaluation**: `"Successfully processed evaluation results for block {block_id}"`
4. **Feedback Generation**: `"Successfully generated and stored AI feedback for block {block_id}"`
5. **Frontend Polling**: `"Failed to fetch enhanced results: {error}"`

### 11.2 Debug Information
- Database queries and results
- API request/response data
- Background task execution status
- Topic memory processing updates

---

## 12. COMMON ISSUES AND SOLUTIONS

### 12.1 "No current exercises found"
**Cause**: User has no exercise data in database
**Solution**: Generate new exercises via `/api/training-exercises`

### 12.2 "Exercise results not found"
**Cause**: Polling before background evaluation completes
**Solution**: Continue polling, results will appear when ready

### 12.3 "Block ID mismatch"
**Cause**: Frontend using wrong block ID for polling
**Solution**: Use `block_id` from API response, not hardcoded "training"

### 12.4 "Feedback not loading"
**Cause**: Background evaluation failed or timed out
**Solution**: Check backend logs for evaluation errors

---

## 13. TESTING CHECKLIST

### 13.1 Frontend Tests
- [ ] Submit button enables when all exercises answered
- [ ] Progress bar shows during submission
- [ ] Results appear after submission
- [ ] Detailed feedback loads progressively
- [ ] Continue button appears when complete

### 13.2 Backend Tests
- [ ] Training submission accepts valid data
- [ ] Block ID extraction works correctly
- [ ] Background evaluation completes
- [ ] Results endpoint returns data
- [ ] Database storage works correctly

### 13.3 Integration Tests
- [ ] Complete flow from submission to feedback
- [ ] Error handling for network issues
- [ ] Timeout handling for long evaluations
- [ ] Topic memory integration
- [ ] Session persistence across requests

---

This documentation provides a complete trace of the feedback flow. When you encounter issues, check the logs at each step to identify where the flow breaks down.
