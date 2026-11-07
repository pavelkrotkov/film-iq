import assert from "node:assert/strict";
import { accessibleProjects, projectUrl } from "./project_picker.js";

const workspace = [{id: "w", name: "Synthetic"}];
const projects = [{id: "a", name: "Allowed"}, {id: "b", name: "Excluded"}];
const mock = (access) => async (path) => {
  if (path === "/workspace") return workspace;
  if (path.endsWith("/project-access/me")) return access;
  if (path === "/project?workspaceId=w") return projects;
  throw new Error("Unexpected request");
};
assert.deepEqual((await accessibleProjects(mock({projectAccess:"selected", projectIds:["a"]}))).projects.map((p) => p.id), ["a"]);
assert.deepEqual((await accessibleProjects(mock({projectAccess:"all", projectIds:[]}))).projects.map((p) => p.id), ["a", "b"]);
const malformed = await accessibleProjects(mock({projectAccess:"invalid", projectIds:[]}));
assert.deepEqual(malformed.projects, []);
assert.equal(malformed.incomplete, true);
const denied = await accessibleProjects(async (path) => path === "/workspace" ? workspace : Promise.reject(new Error("denied")));
assert.deepEqual(denied.projects, []);
assert.equal(denied.incomplete, true);
await assert.rejects(() => accessibleProjects(async () => { throw new Error("unauthenticated"); }));
assert.equal(projectUrl("http://localhost:15174/?project=a#film=one", "a"), "http://localhost:15174/?project=a#film=one");
assert.equal(projectUrl("http://localhost:15174/?project=a#film=one", "b"), "http://localhost:15174/?project=b");
console.log("Authenticated project picker access and failure checks passed");
