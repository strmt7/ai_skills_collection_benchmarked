# Microsoft.Azure.WebJobs.Extensions.AuthenticationEvents SDK Acceptance Criteria (.NET)

**SDK**: `Microsoft.Azure.WebJobs.Extensions.AuthenticationEvents`
**Repository**: https://github.com/Azure/azure-sdk-for-net/tree/main/sdk/entra/Microsoft.Azure.WebJobs.Extensions.AuthenticationEvents
**Package**: https://www.nuget.org/packages/Microsoft.Azure.WebJobs.Extensions.AuthenticationEvents
**Purpose**: Skill testing acceptance criteria for validating generated C# code correctness

---

## 1. Correct Using Statements

### 1.1 Core Imports

#### ✅ CORRECT: Token Issuance Events
```csharp
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.AuthenticationEvents;
using Microsoft.Azure.WebJobs.Extensions.AuthenticationEvents.TokenIssuanceStart;
using Microsoft.Extensions.Logging;
```

#### ✅ CORRECT: Attribute Collection Events
```csharp
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.AuthenticationEvents;
using Microsoft.Azure.WebJobs.Extensions.AuthenticationEvents.Framework;
using Microsoft.Extensions.Logging;
```

### 1.2 Anti-Patterns (ERRORS)

#### ❌ INCORRECT: Using non-existent namespaces
```csharp
// WRONG - These don't exist
using Microsoft.Entra.AuthenticationEvents;
using Azure.Functions.AuthenticationEvents;
```

---

## 2. Token Issuance Event Patterns

### 2.1 ✅ CORRECT: Add Custom Claims
```csharp
[FunctionName("OnTokenIssuanceStart")]
public static WebJobsAuthenticationEventResponse Run(
    [WebJobsAuthenticationEventsTrigger] WebJobsTokenIssuanceStartRequest request,
    ILogger log)
{
    var response = new WebJobsTokenIssuanceStartResponse();

    response.Actions.Add(new WebJobsProvideClaimsForToken
    {
        Claims = new Dictionary<string, string>
        {
            { "customClaim1", "customValue1" },
            { "department", "Engineering" }
        }
    });

    return response;
}
```

### 2.2 Anti-Patterns (ERRORS)

#### ❌ INCORRECT: Wrong trigger attribute
```csharp
// WRONG - Use WebJobsAuthenticationEventsTrigger
[HttpTrigger] WebJobsTokenIssuanceStartRequest request
```

#### ❌ INCORRECT: Wrong return type
```csharp
// WRONG - Must return WebJobsAuthenticationEventResponse
public static string Run(...)
```

---

## 3. Attribute Collection Patterns

### 3.1 ✅ CORRECT: Prefill Values
```csharp
response.Actions.Add(new WebJobsSetPrefillValues
{
    Attributes = new Dictionary<string, string>
    {
        { "city", "Seattle" }
    }
});
```

### 3.2 ✅ CORRECT: Show Block Page
```csharp
response.Actions.Add(new WebJobsShowBlockPage
{
    Message = "Sign-up is currently disabled."
});
```

### 3.3 ✅ CORRECT: Validation Error
```csharp
response.Actions.Add(new WebJobsShowValidationError
{
    Message = "Display name must be at least 3 characters.",
    AttributeErrors = new Dictionary<string, string>
    {
        { "displayName", "Name is too short" }
    }
});
```

### 3.4 ✅ CORRECT: Modify Attributes
```csharp
response.Actions.Add(new WebJobsModifyAttributeValues
{
    Attributes = new Dictionary<string, string>
    {
        { "displayName", displayName.Trim() }
    }
});
```

---

## 4. OTP Event Patterns

### 4.1 ✅ CORRECT: OTP Send Success
```csharp
response.Actions.Add(new WebJobsOnOtpSendSuccess());
```

### 4.2 ✅ CORRECT: OTP Send Failed
```csharp
response.Actions.Add(new WebJobsOnOtpSendFailed
{
    Error = "Failed to send verification code"
});
```

---

## 5. Error Handling Patterns

### 5.1 ✅ CORRECT: Graceful Error Handling
```csharp
try
{
    // Your logic
    return response;
}
catch (Exception ex)
{
    log.LogError(ex, "Error processing event");
    return new WebJobsTokenIssuanceStartResponse();
}
```

---

## 6. Key Types Reference

| Type | Purpose |
|------|---------|
| `WebJobsAuthenticationEventsTriggerAttribute` | Function trigger |
| `WebJobsTokenIssuanceStartRequest` | Token issuance request |
| `WebJobsTokenIssuanceStartResponse` | Token issuance response |
| `WebJobsProvideClaimsForToken` | Add claims action |
| `WebJobsAttributeCollectionStartRequest` | Attribute collection start request |
| `WebJobsAttributeCollectionSubmitRequest` | Attribute submission request |
| `WebJobsSetPrefillValues` | Prefill form values |
| `WebJobsShowBlockPage` | Block user |
| `WebJobsShowValidationError` | Show validation errors |
| `WebJobsModifyAttributeValues` | Modify submitted values |
| `WebJobsOnOtpSendRequest` | OTP send request |
| `WebJobsOnOtpSendSuccess` | OTP sent successfully |
| `WebJobsOnOtpSendFailed` | OTP send failed |
| `WebJobsContinueWithDefaultBehavior` | Continue default flow |

## 7. Supported Events

| Event | Purpose |
|-------|---------|
| `OnTokenIssuanceStart` | Add custom claims to tokens |
| `OnAttributeCollectionStart` | Customize attribute collection UI |
| `OnAttributeCollectionSubmit` | Validate/modify submitted attributes |
| `OnOtpSend` | Custom OTP delivery |

---

## 8. Best Practices Summary

1. **Validate all inputs** — Never trust request data
2. **Handle errors gracefully** — Return appropriate responses
3. **Log correlation IDs** — For troubleshooting
4. **Keep functions fast** — Authentication events have timeouts
5. **Use managed identity** — For secure Azure resource access
6. **Test locally** — With Azure Functions Core Tools
7. **Don't throw exceptions** — Return empty response instead
