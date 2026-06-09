import { useQuery } from "@tanstack/react-query"
import { get } from "@/api/client"

interface BackBuildInfo {
  git_hash: string
  build_time: string
}

export function useBuildInfo() {
  const { data: back } = useQuery<BackBuildInfo>({
    queryKey: ["build-info"],
    queryFn: () => get<BackBuildInfo>("/build-info"),
    staleTime: Infinity,
  })

  return {
    front: { gitHash: __FRONT_GIT_HASH__, buildTime: __FRONT_BUILD_TIME__ },
    back,
  }
}
