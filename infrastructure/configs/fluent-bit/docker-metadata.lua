-- base version from https://github.com/fluent/fluent-bit/issues/1499
DOCKER_VAR_DIR = '/var/lib/docker/containers/'
DOCKER_CONTAINER_CONFIG_FILE = '/config.v2.json'
CACHE_TTL_SEC = 300

DOCKER_CONTAINER_METADATA = {
  ['container_name'] = '\"Name\":\"/?(.-)\"',
  ['container_image'] = '\"Image\":\"/?(.-)\"',
}

cache = {}

-- Apply regular expression map to the given string
function apply_regex_map(data_tbl, reg_tbl, func, str)
  if str then
    for key, regex in pairs(reg_tbl) do
        data_tbl[key] = func(str, regex)
    end
  else
    for key, regex in pairs(reg_tbl) do
      local tbl = {}
      for k, v in func(data_tbl[key], regex) do
        tbl[k] = v
      end
      data_tbl[key] = tbl
    end
  end
  return data_tbl
end

-- Get container id from tag (works for Docker Compose)
function get_container_id_from_tag(tag)
  return string.match(tag, 'containers%.([a-f0-9]+)%.')
end

-- Gets metadata from config.v2.json file for container
function get_container_metadata_from_disk(container_id)
  local docker_config_file = DOCKER_VAR_DIR .. container_id .. DOCKER_CONTAINER_CONFIG_FILE
  fl = io.open(docker_config_file, 'r')
  if fl == nil then
    return nil
  end

  -- parse json file and create record for cache
  local data = { time = os.time() }
  local reg_match = string.match
  local reg_gmatch = string.gmatch
  for line in fl:lines() do
    data = apply_regex_map(
      data,
      DOCKER_CONTAINER_METADATA,
      reg_match,
      line
    )
  end
  fl:close()

  if next(data) == nil then
    return nil
  else
    return data
  end
end

function enrich_with_docker_metadata(tag, timestamp, record)
  -- Get container id from tag
  container_id = get_container_id_from_tag(tag)
  if not container_id then
    return 0, timestamp, record
  end

  -- Add container_id to record
  new_record = record
  new_record['container_id'] = container_id

  -- Check if we have fresh cache record for container
  local cached_data = cache[container_id]
  if cached_data == nil or ( os.time() - cached_data['time'] > CACHE_TTL_SEC) then
    cached_data = get_container_metadata_from_disk(container_id)
    cache[container_id] = cached_data
    new_record['metadata_source'] = 'disk'
  else
    new_record['metadata_source'] = 'cache'
  end

  -- Metadata found in cache or got from disk, enrich record
  if cached_data then
    for key, regex in pairs(DOCKER_CONTAINER_METADATA) do
      new_record[key] = cached_data[key]
    end
  end

  return 2, timestamp, new_record
end

function extract_service_name_from_container_name(tag, timestamp, record)
  container_name = record['container_name']
  if not container_name then
    return 0, timestamp, record
  end

  -- strip off trailing -<index> if it exists
  new_record = record
  local service_name = string.match(container_name, '^(.-)-%d+$') or container_name
  new_record['service_name'] = service_name
  return 2, timestamp, new_record
end
