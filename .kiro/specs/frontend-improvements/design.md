# Design Document

## Overview

This design document outlines the implementation approach for enhancing the AI Test Case Generator frontend with collapsible instructions, message timestamps, conversation persistence, and integrated download functionality. The design maintains the existing architecture while adding these user experience improvements.

## Architecture

The current frontend follows a modular JavaScript architecture with:
- **DOM Element Management**: Centralized element references in `elements` object
- **Event-Driven Architecture**: Event listeners for user interactions
- **State Management**: Global variables for session and UI state
- **API Communication**: Fetch-based HTTP requests to backend services

### Component Structure
```
Frontend Architecture
├── HTML Template (index.html)
├── CSS Styling (styles.css)  
├── JavaScript Logic (script.js)
│   ├── Initialization & Configuration
│   ├── UI State Management
│   ├── Event Handlers
│   ├── API Communication
│   └── DOM Manipulation
```

## Components and Interfaces

### 1. Collapsible Instructions Panel

**Component**: `CollapsibleInstructions`
- **Location**: `.tips-card` element in left sidebar
- **State**: `instructionsExpanded` boolean flag
- **Methods**:
  - `toggleInstructions()`: Toggle expanded/collapsed state
  - `initializeInstructionsState()`: Set default collapsed state on page load

**Interface Changes**:
```html
<div class="tips-card collapsible" id="instructionsCard">
  <div class="tips-header clickable" id="instructionsHeader">
    <svg class="info-icon">...</svg>
    <span>操作说明</span>
    <svg class="expand-icon" id="instructionsExpandIcon">...</svg>
  </div>
  <div class="tips-content" id="instructionsContent">
    <ul class="tips-list">...</ul>
  </div>
</div>
```

### 2. Message Timestamp System

**Component**: `MessageTimestamp`
- **Integration**: Modify `addMessage()` function
- **Format**: HH:MM for same day, MM-DD HH:MM for different days
- **Storage**: Add timestamp to message data structure

**Enhanced Message Structure**:
```javascript
const messageData = {
  text: string,
  type: 'ai' | 'user',
  timestamp: Date,
  id: string
}
```

**Interface Changes**:
```html
<div class="message ai-message">
  <div class="message-avatar">Agent</div>
  <div class="message-content">
    <div class="message-text">...</div>
    <div class="message-timestamp">14:32</div>
  </div>
</div>
```

### 3. Conversation Persistence Manager

**Component**: `ConversationManager`
- **State**: `conversationHistory` array to store messages
- **Methods**:
  - `preserveConversation()`: Maintain existing messages
  - `addSessionSeparator()`: Add visual separator for new sessions
  - `clearConversation()`: Optional method for complete reset

**Session Management**:
- Modify `startGeneration()` to check for existing conversation
- Add session separator when starting new generation with existing history
- Maintain scroll position and message ordering

### 4. Integrated Download Card

**Component**: `DownloadCard`
- **Trigger**: Replace `showActionButtons()` download button logic
- **Integration**: Render as chat message with special styling
- **Methods**:
  - `createDownloadCard()`: Generate download card HTML
  - `handleDownloadClick()`: Process download action
  - `showDownloadFeedback()`: Provide user feedback

**Download Card Structure**:
```html
<div class="message ai-message">
  <div class="message-avatar">Agent</div>
  <div class="message-content">
    <div class="download-card" id="downloadCard">
      <div class="download-card-header">
        <svg class="download-icon">...</svg>
        <div class="download-info">
          <h4>测试用例文件已生成</h4>
          <span class="file-details">test_cases_2024-01-08.xml (2.3 KB)</span>
        </div>
      </div>
      <button class="download-button" id="downloadFileBtn">
        <svg class="download-btn-icon">...</svg>
        <span>下载文件</span>
      </button>
    </div>
  </div>
</div>
```

## Data Models

### Enhanced Message Model
```javascript
interface Message {
  id: string;
  text: string;
  type: 'ai' | 'user' | 'system';
  timestamp: Date;
  metadata?: {
    sessionId?: string;
    isSessionStart?: boolean;
    downloadInfo?: DownloadInfo;
  };
}

interface DownloadInfo {
  fileId: string;
  fileName: string;
  fileSize: string;
  downloadUrl: string;
}
```

### UI State Model
```javascript
interface UIState {
  instructionsExpanded: boolean;
  conversationHistory: Message[];
  currentSessionId: string | null;
  downloadAvailable: boolean;
  lastMessageTimestamp: Date | null;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Instructions Panel Toggle Behavior
*For any* sequence of clicks on the instructions header, the panel should alternate between expanded and collapsed states, with the visual state always matching the internal state
**Validates: Requirements 1.2, 1.3, 1.4**

### Property 2: Message Timestamp Consistency
*For any* message added to the chat interface, the system should display a properly formatted timestamp that accurately reflects when the message was created
**Validates: Requirements 2.1, 2.2, 2.3, 2.5**

### Property 3: Conversation History Management
*For any* new generation session started with existing conversation history, all previous messages should be preserved and new messages should be appended while maintaining all original message properties
**Validates: Requirements 3.1, 3.2, 3.3**

### Property 4: Download Card Integration and Replacement
*For any* completed test case generation, the download functionality should appear as an integrated chat card with file information, while removing any separate download buttons from action areas
**Validates: Requirements 4.1, 4.2, 4.4, 4.6**

### Property 5: Download Card Functionality
*For any* displayed download card, clicking it should initiate file download and provide appropriate user feedback
**Validates: Requirements 4.3, 4.5**

### Property 6: Existing Functionality Preservation
*For any* existing feature (upload, configuration, message rendering, session management), the functionality should continue to work correctly after implementing the new improvements
**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

## Error Handling

### Instructions Panel Errors
- **Animation Failures**: Fallback to instant show/hide if CSS transitions fail
- **State Desync**: Reset to default collapsed state if inconsistency detected

### Timestamp Errors
- **Invalid Dates**: Display "时间未知" for invalid timestamp values
- **Timezone Issues**: Use local time consistently across all messages

### Conversation Persistence Errors
- **Memory Overflow**: Implement message limit (e.g., 100 messages) with oldest message removal
- **Session Conflicts**: Clear conversation if session ID changes unexpectedly

### Download Card Errors
- **File Not Available**: Display error message within card instead of download button
- **Network Failures**: Provide retry mechanism and clear error feedback

## Testing Strategy

### Unit Testing
- Test individual functions for instructions toggle, timestamp formatting, and download card creation
- Mock DOM elements and verify correct manipulation
- Test edge cases like invalid timestamps and missing file information

### Property-Based Testing
- **Instructions Toggle Property**: Generate random sequences of toggle actions and verify state consistency
- **Timestamp Format Property**: Generate random dates and verify correct formatting across different scenarios
- **Message Persistence Property**: Generate random message sequences and verify preservation across sessions
- **Download Integration Property**: Generate various completion scenarios and verify download card appears correctly

### Integration Testing
- Test complete user workflows including multiple generation sessions
- Verify interaction between new features and existing functionality
- Test responsive behavior across different screen sizes

### Manual Testing Scenarios
- Instructions panel behavior on page load and user interaction
- Message timestamp display across different time periods
- Conversation flow with multiple generation sessions
- Download card functionality and user feedback

## Implementation Notes

### CSS Considerations
- Add transition animations for instructions panel collapse/expand
- Ensure timestamp styling doesn't interfere with existing message layout
- Maintain responsive design with new download card component

### JavaScript Modifications
- Extend existing `addMessage()` function rather than replacing it
- Integrate with current session management without breaking API communication
- Maintain backward compatibility with existing event handlers

### Performance Considerations
- Limit conversation history to prevent memory issues
- Use efficient DOM manipulation for timestamp updates
- Optimize CSS animations for smooth user experience