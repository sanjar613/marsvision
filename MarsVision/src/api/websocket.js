export function connectToAlerts() {
	const socketUrl = new URL('/api/ws/alerts', window.location.href);
	socketUrl.protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
	return new WebSocket(socketUrl);
}
