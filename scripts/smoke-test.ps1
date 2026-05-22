param(
  [string]$Api = "http://127.0.0.1:8010"
)

$ErrorActionPreference = "Stop"

$health = Invoke-RestMethod -Uri "$Api/health"
if ($health.status -ne "ok") {
  throw "API health check failed"
}
$config = Invoke-RestMethod -Uri "$Api/api/dev/config"

$tripBody = @{
  destination = "Hangzhou West Lake"
  duration_minutes = 120
  preferences = @("scenery", "video", "easy")
  use_panorama_camera = $true
} | ConvertTo-Json

$trip = Invoke-RestMethod -Method Post -Uri "$Api/api/trips" -ContentType "application/json" -Body $tripBody
$route = Invoke-RestMethod -Method Post -Uri "$Api/api/trips/$($trip.trip_id)/route"
$media = Invoke-RestMethod -Method Post -Uri "$Api/api/trips/$($trip.trip_id)/media/demo"
$frames = Invoke-RestMethod -Method Post -Uri "$Api/api/media/$($media.media_id)/extract-frames"
$marked = Invoke-RestMethod -Method Post -Uri "$Api/api/frames/$($frames.frames[-1].frame_id)/mark" -ContentType "application/json" -Body (@{ marked = $true; reason = "favorite moment" } | ConvertTo-Json)

$companionBody = @{
  frame_id = $frames.frames[0].frame_id
  route_node_id = $route.nodes[0].id
  user_status = "normal"
} | ConvertTo-Json

$companion = Invoke-RestMethod -Method Post -Uri "$Api/api/trips/$($trip.trip_id)/companion/analyze" -ContentType "application/json" -Body $companionBody
$export = Invoke-RestMethod -Method Post -Uri "$Api/api/trips/$($trip.trip_id)/exports"

[PSCustomObject]@{
  Health = $health.status
  AiMode = $config.ai_mode
  MapMode = $config.map_mode
  TripId = $trip.trip_id
  RouteNodes = $route.nodes.Count
  Frames = $frames.frames.Count
  MarkedFrame = $marked.marked
  CompanionLength = $companion.message.Length
  SelectedFrames = $export.selected_frames.Count
  DraftShots = $export.video_draft.Count
  FirstShotType = $export.video_draft[0].shot_type
  StoryEvents = $export.story_events.Count
}
