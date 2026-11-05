// Only authenticated Kaneo endpoints are used. Fail each workspace closed if
// project access cannot be determined; never guess that an omitted project is public.
export async function accessibleProjects(request) {
  const workspaces = await request("/workspace");
  if (!Array.isArray(workspaces)) throw new Error("Unexpected workspace list");
  const results = await Promise.allSettled(workspaces.map(async (workspace) => {
    if (typeof workspace.id !== "string" || typeof workspace.name !== "string") throw new Error("Invalid workspace");
    const id = encodeURIComponent(workspace.id);
    const [access, projects] = await Promise.all([
      request(`/workspace/${id}/project-access/me`),
      request(`/project?workspaceId=${id}`),
    ]);
    if (!Array.isArray(projects) || !Array.isArray(access?.projectIds) || !["all", "selected"].includes(access?.projectAccess)) throw new Error("Invalid project access");
    const permitted = new Set(access.projectIds);
    return projects
      .filter((project) => typeof project.id === "string" && typeof project.name === "string" && (access.projectAccess === "all" || permitted.has(project.id)))
      .map((project) => ({id: project.id, name: project.name, workspace: workspace.name}));
  }));
  return {
    projects: results.flatMap((result) => result.status === "fulfilled" ? result.value : []),
    incomplete: results.some((result) => result.status === "rejected"),
  };
}

export function projectUrl(currentUrl, project) {
  const next = new URL(currentUrl);
  if (next.searchParams.get("project") !== project) next.hash = "";
  next.searchParams.set("project", project);
  return next.href;
}
