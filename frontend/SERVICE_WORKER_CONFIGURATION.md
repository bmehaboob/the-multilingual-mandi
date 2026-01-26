# Service Worker Configuration

## Overview

This document describes the service worker configuration for the Multilingual Mandi PWA, implementing offline functionality and caching strategies as specified in Requirements 12.7 and 19.1.

## Architecture

### Workbox Configuration

The service worker is configured using Workbox via the `vite-plugin-pwa` plugin. The configuration is defined in `vite.config.ts`.

### Caching Strategies

#### 1. Cache-First Strategy (Static Assets)
**Requirement 19.1**: Cache-first strategy for static assets

Used for assets that rarely change:
- **Images**: PNG, JPG, JPEG, SVG, GIF, WebP, ICO
- **Fonts**: WOFF, WOFF2, TTF, EOT
- **Negotiation Templates**: Cached for 7 days

**Benefits**:
- Instant loading from cache
- Reduced bandwidth usage
- Works completely offline

**Configuration**:
```typescript
{
  handler: 'CacheFirst',
  options: {
    cacheName: 'image-cache',
    expiration: {
      maxEntries: 100,
      maxAgeSeconds: 60 * 60 * 24 * 30 // 30 days
    }
  }
}
```

#### 2. Network-First Strategy (API Calls)
**Requirement 12.7**: Network-first strategy for API calls with fallback

Used for dynamic data that should be fresh:
- **API Endpoints**: All `/api/*` routes
- **Price Data**: Market prices with 24-hour cache
- **Transaction History**: User transactions
- **User Preferences**: Profile and settings

**Benefits**:
- Always tries to fetch fresh data
- Falls back to cache when offline
- Provides stale data rather than no data

**Configuration**:
```typescript
{
  urlPattern: /^https?:\/\/.*\/api\/.*/i,
  handler: 'NetworkFirst',
  options: {
    cacheName: 'api-cache',
    networkTimeoutSeconds: 10,
    expiration: {
      maxEntries: 100,
      maxAgeSeconds: 60 * 60 * 24 // 24 hours
    }
  }
}
```

### Cache Categories

#### 1. API Cache
- **Pattern**: `/api/*`
- **Strategy**: Network First
- **Timeout**: 10 seconds
- **Max Entries**: 100
- **Max Age**: 24 hours
- **Purpose**: General API responses

#### 2. Price Data Cache
- **Pattern**: `/api/prices/*`
- **Strategy**: Network First
- **Timeout**: 5 seconds
- **Max Entries**: 200
- **Max Age**: 24 hours (Requirement 12.2)
- **Purpose**: Market price data for offline access

#### 3. Transaction Cache
- **Pattern**: `/api/transactions/*`
- **Strategy**: Network First
- **Timeout**: 5 seconds
- **Max Entries**: 100
- **Max Age**: 7 days
- **Purpose**: Transaction history (Requirement 12.8)

#### 4. User Data Cache
- **Pattern**: `/api/users/*`
- **Strategy**: Network First
- **Timeout**: 5 seconds
- **Max Entries**: 50
- **Max Age**: 30 days
- **Purpose**: User preferences (Requirement 12.5)

#### 5. Template Cache
- **Pattern**: `/api/templates/*`
- **Strategy**: Cache First
- **Max Entries**: 50
- **Max Age**: 7 days
- **Purpose**: Negotiation templates (Requirement 12.6)

#### 6. Image Cache
- **Pattern**: Image file extensions
- **Strategy**: Cache First
- **Max Entries**: 100
- **Max Age**: 30 days
- **Purpose**: Static images

#### 7. Font Cache
- **Pattern**: Font file extensions
- **Strategy**: Cache First
- **Max Entries**: 20
- **Max Age**: 1 year
- **Purpose**: Web fonts

#### 8. Audio Cache
- **Pattern**: Audio file extensions
- **Strategy**: Network First
- **Timeout**: 10 seconds
- **Max Entries**: 50
- **Max Age**: 24 hours
- **Purpose**: TTS audio (deleted after processing per Requirement 15.2)

## Service Worker Registration

### Registration Flow

1. **Check Environment**: Only registers in production or when `VITE_SW_DEV` is set
2. **Create Workbox Instance**: Initialize Workbox with `/sw.js`
3. **Register Event Listeners**: Listen for installation, activation, and updates
4. **Monitor Network Status**: Track online/offline transitions

### Event Handling

#### Installation
- First-time installation: Triggers `onSuccess` callback
- Update installation: Triggers `onUpdate` callback

#### Activation
- New service worker takes control
- Old caches are cleaned up

#### Updates
- New version detected: Shows update notification
- User can trigger update: Calls `skipWaiting()`

### Network Status Monitoring
**Requirement 12.4**: Notify users when operating in offline mode

- Listens to `online` and `offline` events
- Updates UI state immediately
- Triggers appropriate callbacks

## React Integration

### useServiceWorker Hook

Provides service worker state and actions:

```typescript
const [state, actions] = useServiceWorker();

// State
state.isOnline          // Network status
state.isUpdateAvailable // Update notification
state.isInstalled       // SW installation status
state.cacheStats        // Cache statistics

// Actions
actions.updateServiceWorker()  // Apply update
actions.refreshCacheStats()    // Get cache info
```

### useOnlineStatus Hook

Simple hook for offline detection:

```typescript
const isOnline = useOnlineStatus();
```

### OfflineIndicator Component

Visual component for offline status and updates:

```tsx
<OfflineIndicator />
```

Features:
- Offline banner at top (orange)
- Update banner at bottom (blue)
- Accessible with ARIA attributes
- Auto-updates based on network status

## Cache Management

### Automatic Cleanup

- **Old Caches**: Automatically removed on activation
- **Expired Entries**: Removed based on `maxAgeSeconds`
- **Size Limits**: Enforced via `maxEntries`

### Manual Operations

```typescript
// Clear all caches
await clearAllCaches();

// Get cache statistics
const stats = await getCacheStats();
console.log(stats.cacheNames);  // ['api-cache', 'image-cache', ...]
console.log(stats.totalSize);   // Total bytes cached
```

## Offline Functionality

### What Works Offline

1. **Static Assets**: All HTML, CSS, JS, images, fonts
2. **Cached API Data**: Previously fetched data
3. **Price Information**: Last 24 hours of price data
4. **Transaction History**: Recent transactions
5. **User Preferences**: Stored locally
6. **Negotiation Templates**: Pre-cached templates

### What Requires Network

1. **New API Requests**: First-time data fetches
2. **Voice Processing**: STT, Translation, TTS services
3. **Real-time Updates**: Live price changes
4. **Authentication**: Voice biometric verification

### Offline Message Queue
**Requirement 12.1**: Queue messages for later transmission

Handled by `OfflineSyncManager` (Task 15.2):
- Messages recorded while offline
- Stored in IndexedDB
- Auto-synced when online

## Performance Optimization

### Bundle Size

- Service worker: ~50KB (Workbox runtime)
- Registration code: ~5KB
- Total overhead: <60KB

### Cache Size Limits

- **Total Precache**: ~2MB maximum
- **Runtime Caches**: Varies by usage
- **Automatic Cleanup**: Prevents unlimited growth

### Network Timeouts

- **API Calls**: 10 seconds
- **Price Data**: 5 seconds
- **User Data**: 5 seconds
- **Audio**: 10 seconds

## Testing

### Unit Tests

- `serviceWorkerRegistration.test.ts`: Core functionality
- `useServiceWorker.test.tsx`: React hook
- `OfflineIndicator.test.tsx`: UI component

### Test Coverage

- ✅ Online/offline detection
- ✅ Service worker registration
- ✅ Update notifications
- ✅ Cache management
- ✅ Event handling
- ✅ Accessibility

### Manual Testing

1. **Offline Mode**:
   - Open DevTools → Network → Offline
   - Verify offline banner appears
   - Test cached data access

2. **Update Flow**:
   - Build new version
   - Deploy
   - Verify update notification
   - Click "Update Now"
   - Verify page reloads

3. **Cache Inspection**:
   - Open DevTools → Application → Cache Storage
   - Verify cache entries
   - Check expiration

## Troubleshooting

### Service Worker Not Registering

- Check browser support: `'serviceWorker' in navigator`
- Verify HTTPS (required for SW)
- Check console for errors
- Ensure `/sw.js` is accessible

### Offline Mode Not Working

- Verify service worker is active
- Check cache entries in DevTools
- Ensure network is actually offline
- Check cache patterns match URLs

### Update Not Applying

- Hard refresh: Ctrl+Shift+R
- Clear service worker: DevTools → Application → Service Workers → Unregister
- Clear caches manually
- Check `skipWaiting` is called

### Cache Growing Too Large

- Verify `maxEntries` limits
- Check `maxAgeSeconds` expiration
- Use `clearAllCaches()` if needed
- Monitor with `getCacheStats()`

## Best Practices

1. **Always Test Offline**: Use DevTools offline mode
2. **Monitor Cache Size**: Use `getCacheStats()` regularly
3. **Handle Updates Gracefully**: Show clear UI for updates
4. **Provide Feedback**: Show offline indicators
5. **Cache Strategically**: Balance freshness vs. offline access
6. **Set Appropriate TTLs**: Match data volatility
7. **Clean Up Old Data**: Use expiration policies
8. **Test on Real Devices**: Especially 2G/3G networks

## Requirements Mapping

| Requirement | Implementation |
|-------------|----------------|
| 12.2 | Price data cached for 24 hours |
| 12.4 | Offline mode detection and notification |
| 12.5 | User preferences stored locally |
| 12.6 | Negotiation templates cached |
| 12.7 | Service workers for offline functionality |
| 12.8 | Transaction history cached offline |
| 19.1 | PWA with service workers |

## Future Enhancements

1. **Background Sync**: Queue failed requests for retry
2. **Push Notifications**: Alert users of price changes
3. **Periodic Sync**: Update price data in background
4. **Advanced Caching**: Predictive prefetching
5. **Offline Analytics**: Track offline usage patterns

## References

- [Workbox Documentation](https://developers.google.com/web/tools/workbox)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [PWA Best Practices](https://web.dev/pwa/)
- [vite-plugin-pwa](https://vite-pwa-org.netlify.app/)
